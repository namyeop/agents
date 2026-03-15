# 에이전트 크루 설계 및 실행 계획

본 문서는 CrewAI로 스레드형 글을 작성하고(3가지 후보), 바이럴 스코어를 산출·검증하는 전체 아키텍처와 구현 계획을 설명합니다. Firecrawl Search API를 통한 밈/키워드 리서치와 Pydantic 기반의 최종 출력 형식을 포함합니다.

## 목표

- 스레드 글 3가지 후보(보수/중간/공격적) 생성
- 각 후보에 대한 바이럴 스코어(총점 + 세부 지표) 산출
- 심사 에이전트가 점수 타당성을 검토하고 개선안을 제공
- 최종 결과물을 Pydantic 모델로 엄격히 직렬화(JSON)

## 전체 흐름(파이프라인)

1. meme_research_task: Firecrawl로 최신 밈/키워드/문화 코드 리서치 → 정제된 인사이트 반환
2. write_thread_task × 3: 동일 리서치 컨텍스트로 톤/전략 차이를 둔 3가지 후보 작성(보수/중간/공격적)
3. viral_score_task × 3: 각 후보에 대해 세부 지표별 가중치로 점수 산출 + 개선 포인트 제시(JSON)
4. review_and_judge_task: 상위 후보들의 강·약점 진단, 리라이트 제안, 점수 타당성 검토/보정 의견
5. Pydantic 검증: 후보/점수/리뷰를 엄격 검증 후 `FinalOutput`으로 직렬화

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
- 구현 위치: `writing_agents/tools.py`에 래퍼 추가, CrewAI Tool로 등록해 `trend_spotter_agent`가 사용

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
