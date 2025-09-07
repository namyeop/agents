# 에이전트 크루 설계 및 실행 계획

본 문서는 CrewAI로 스레드형 글을 작성하고(3가지 후보), 바이럴 스코어를 산출·검증하는 전체 아키텍처와 구현 계획을 설명합니다. Firecrawl Search API를 통한 밈/키워드 리서치와 Pydantic 기반의 최종 출력 형식을 포함합니다.

## 목표
- 스레드 글 3가지 후보(보수/중간/공격적) 생성
- 각 후보에 대한 바이럴 스코어(총점 + 세부 지표) 산출
- 심사 에이전트가 점수 타당성을 검토하고 개선안을 제공
- 최종 결과물을 Pydantic 모델로 엄격히 직렬화(JSON)

## 전체 흐름(파이프라인)
1) meme_research_task: Firecrawl로 최신 밈/키워드/문화 코드 리서치 → 정제된 인사이트 반환
2) write_thread_task × 3: 동일 리서치 컨텍스트로 톤/전략 차이를 둔 3가지 후보 작성(보수/중간/공격적)
3) viral_score_task × 3: 각 후보에 대해 세부 지표별 가중치로 점수 산출 + 개선 포인트 제시(JSON)
4) review_and_judge_task: 상위 후보들의 강·약점 진단, 리라이트 제안, 점수 타당성 검토/보정 의견
5) Pydantic 검증: 후보/점수/리뷰를 엄격 검증 후 `FinalOutput`으로 직렬화

## 컴포넌트 개요
- Agents (YAML):
  - hooksmith_agent: 강력한 훅·제목 작성
  - trend_spotter_agent: 밈/키워드 트렌드 리서치(Firecrawl 도구 사용)
  - meme_crafter_agent: 밈/한줄 카피 강화(옵션, 도구 사용 가능)
  - debate_curator_agent: 안전한 논쟁 프레이밍(옵션)
  - reply_driver_agent: CTA 설계(옵션)
  - quality_judge_agent: 점수 산출/심사/개선안

- Tasks (YAML):
  - meme_research_task: Firecrawl 기반 리서치 결과 생성
  - write_thread_task: 스레드 초안 작성(리서치 컨텍스트 사용)
  - viral_score_task: 점수/근거/개선 제안(JSON)
  - review_and_judge_task: 종합 심사 및 리라이트 제안

## Firecrawl 도구 설계
- 목적: 밈/키워드/문화 코드 리서치(검색 + 간단 스니펫 수집)
- 의존성/설정:
  - 환경변수: `FIRECRAWL_API_KEY`
  - 엔드포인트: Firecrawl Search API (서치용)
  - 제한/정책: 타임아웃(예: 8~12s), 재시도(예: 2~3회 with 지수 백오프), 쿼터 보호
- 인터페이스(의도):
  - 입력: `query: str`, `language: str`, `limit: int = 5`
  - 출력: `[{title, url, snippet}]`의 간단 리스트
- 구현 위치: `agents/tools.py`에 래퍼 추가, CrewAI Tool로 등록해 `trend_spotter_agent`가 사용

예시 스켈레톤(Python):

```python
# agents/tools.py
import os, time, json
import requests

class FirecrawlSearchTool:
    def __init__(self, api_key: str | None = None, timeout: int = 10):
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.timeout = timeout

    def search(self, query: str, language: str = "ko", limit: int = 5):
        assert self.api_key, "FIRECRAWL_API_KEY is required"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"query": query, "lang": language, "limit": limit}
        backoff = 1
        for attempt in range(3):
            try:
                resp = requests.post("https://api.firecrawl.com/search", headers=headers, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                # 정규화: [{title, url, snippet}]
                items = []
                for it in data.get("results", [])[:limit]:
                    items.append({
                        "title": it.get("title", ""),
                        "url": it.get("url", ""),
                        "snippet": it.get("snippet", "")
                    })
                return items
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(backoff)
                backoff *= 2
```

CrewAI Tool 바인딩(의도):
- `trend_spotter_agent`의 tools 목록에 `FirecrawlSearchTool().search`를 연결하여 `meme_research_task` 내부 프롬프트에서 호출할 수 있도록 설정

## Pydantic 모델 설계
최종 산출물을 엄격히 검증하기 위한 모델 정의를 `agents/models.py`에 추가합니다.

```python
# agents/models.py
from pydantic import BaseModel, Field, HttpUrl, conint
from typing import List, Optional, Literal

class ViralBreakdown(BaseModel):
    hook: conint(ge=0, le=100)
    novelty: conint(ge=0, le=100)
    clarity: conint(ge=0, le=100)
    shareability: conint(ge=0, le=100)
    comment_bait: conint(ge=0, le=100)

class ViralScore(BaseModel):
    total: conint(ge=0, le=100)
    breakdown: ViralBreakdown
    rationale: str
    improvements: List[str]

class ThreadCandidate(BaseModel):
    id: Literal["conservative", "balanced", "aggressive"]
    title: str
    body: List[str]  # 포인트별 줄
    memes: List[str] = []
    cta: str
    platform: str

class Review(BaseModel):
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    rewrites: dict  # {"conservative": str, "balanced": str, "aggressive": str}
    final_recommendation: str
    score_review: str  # 점수 타당성/보정 의견

class FinalOutput(BaseModel):
    topic: str
    target_audience: str
    platform: str
    candidates: List[ThreadCandidate]
    scores: List[ViralScore]  # candidates 순서와 매칭
    review: Review
```

검증/직렬화 예시:

```python
# agents/agent.py 내 최종단
from agents.models import FinalOutput
final = FinalOutput(
    topic=inputs["topic"],
    target_audience=inputs["target_audience"],
    platform=inputs["platform"],
    candidates=candidates,
    scores=scores,
    review=review,
)
print(final.model_dump_json(ensure_ascii=False, indent=2))
```

## YAML 업데이트(Tasks)
이미 존재하는 `write_thread_task`, `viral_score_task`, `review_and_judge_task`에 더해, 리서치 태스크를 추가합니다.

```yaml
# agents/config/tasks.yml
meme_research_task:
  description: >
    Firecrawl 검색으로 최신 밈/키워드/문화 코드를 수집·요약한다. 플랫폼/타깃에 맞는 로컬라이즈 기준을 포함.
  expected_output: >
    {"insights": ["..."], "keywords": ["..."], "references": [{"title": "...", "url": "..."}]}
  agent: trend_spotter_agent
  input_vars: [topic, platform, target_audience]
  verbose: true

write_thread_task:
  # 기존 정의 유지하되 아래처럼 컨텍스트 연결
  context: [meme_research_task]

viral_score_task:
  # 기존 정의 유지(입력은 write_thread_task 결과)

review_and_judge_task:
  # 기존 정의 유지(입력은 write_thread_task, viral_score_task 결과)
```

## 에이전트-툴 연결
- `agents/agent.py`에서 Crew/Agent 생성 시 `trend_spotter_agent`에 Firecrawl 도구를 바인딩
- 필요 시 `meme_crafter_agent`에도 동일 도구를 추가해 문구/밈의 정확도 향상

## 파이프라인 실행(의도 코드)

```python
# agents/agent.py
from crewai import Crew
from agents.tools import FirecrawlSearchTool
from agents.models import FinalOutput

class WritingCrew:
    def crew(self):
        # 1) 에이전트/태스크 로딩(YAML)
        # 2) trend_spotter_agent.tools = [FirecrawlSearchTool().search]
        # 3) meme_research_task 실행 → insights
        # 4) write_thread_task를 conservative/balanced/aggressive 톤으로 3회 실행
        # 5) 각 결과에 대해 viral_score_task 실행
        # 6) review_and_judge_task 실행(상위 후보 또는 전체)
        # 7) Pydantic(FinalOutput)으로 검증/직렬화
        pass
```

톤 분기(예):
- conservative: 보수적·정보 전달형, clickbait 최소화, 정확성/신뢰 우선
- balanced: 공감/흥미와 정보 균형, 대중적 용어와 안전한 논쟁 포인트 포함
- aggressive: 강한 훅/대조/순위·가정법 프레이밍, 과장·인신공격 금지

## 출력 형식(최종 JSON)
- `FinalOutput` 스키마를 준수하며, 후보 3개, 각 스코어, 리뷰 1개를 포함
- 정렬: candidates와 scores의 순서는 동일(각 인덱스 매칭)

## 에러 처리/품질 가이드
- Firecrawl: 타임아웃/HTTP 오류 시 지수 백오프 3회 재시도, 마지막 실패 시 깔끔한 오류 메시지
- 입력 정상화: topic/platform/target_audience 최소 유효성 검사
- 안전성: 과도한 클릭베이트, 허위·과장, 인신공격, 저작권 침해 회피
- 로깅: 요청/응답 요약 로그(민감정보/키 제외)

## 환경변수/설정
- `FIRECRAWL_API_KEY`: Firecrawl 인증 토큰
- 필요 시 `REQUEST_TIMEOUT`, `FIRECRAWL_LIMIT` 등 설정값을 `.env`로 분리

## 향후 확장
- 플랫폼별 템플릿(Threads, X, 블로그 등) 파라미터화
- A/B 테스트 자동 루프(실사용 데이터 반영) 후 가중치 튜닝
- 이미지/짤 생성 도구 연동 및 저작권 필터 추가

