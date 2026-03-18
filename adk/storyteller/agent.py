import json
import base64
from pathlib import Path

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools import ToolContext
from openai import OpenAI
from pydantic import BaseModel, Field


# ── 구조화된 스토리 스키마 ──────────────────────────────────────────

class StoryPage(BaseModel):
    page_number: int = Field(description="페이지 번호 (1-5)")
    text: str = Field(description="어린이 동화 본문 (2-4문장, 한국어)")
    visual_description: str = Field(
        description="이 페이지의 삽화를 묘사하는 영어 프롬프트. "
        "children's book illustration style로 작성"
    )


class Story(BaseModel):
    title: str = Field(description="동화 제목 (한국어)")
    pages: list[StoryPage] = Field(description="5페이지 분량의 동화")


# ── Story Writer Agent ──────────────────────────────────────────────

story_writer = Agent(
    name="story_writer",
    model="gemini-3.0-flash",
    instruction="""당신은 어린이 동화 작가입니다.
사용자가 제시한 테마를 바탕으로 5페이지 분량의 어린이 동화를 작성하세요.

규칙:
- 각 페이지는 2~4문장의 한국어 본문(text)을 포함합니다.
- 각 페이지에는 삽화를 위한 시각 설명(visual_description)을 영어로 작성합니다.
  예: "A small rabbit wearing a red scarf walking through a snowy forest, children's book illustration style, soft watercolor"
- 이야기는 기승전결 구조를 갖추어야 합니다.
- 어린이(5~8세)가 이해할 수 있는 쉬운 한국어를 사용하세요.
- 반드시 정확히 5페이지를 작성하세요.""",
    output_schema=Story,
    output_key="story_data",
)


# ── Illustrator Agent 도구 ──────────────────────────────────────────

def generate_illustrations(tool_context: ToolContext) -> str:
    """State에서 story_data를 읽어 각 페이지의 이미지를 생성합니다.

    Returns:
        생성 결과 요약 메시지
    """
    raw = tool_context.state.get("story_data")
    if not raw:
        return "오류: story_data가 State에 없습니다. Story Writer가 먼저 실행되어야 합니다."

    # output_schema 사용 시 JSON 문자열로 저장됨
    if isinstance(raw, str):
        story = Story.model_validate_json(raw)
    else:
        story = Story.model_validate(raw)

    client = OpenAI()
    results = []

    for page in story.pages:
        prompt = (
            f"{page.visual_description}, "
            "children's book illustration, soft pastel colors, whimsical, friendly"
        )
        try:
            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
            image_b64 = response.data[0].b64_json
            # 이미지를 파일로 저장
            output_dir = Path("generated_stories") / story.title
            output_dir.mkdir(parents=True, exist_ok=True)
            image_path = output_dir / f"page_{page.page_number}.png"
            image_path.write_bytes(base64.b64decode(image_b64))

            results.append(
                f"📖 페이지 {page.page_number}: 이미지 생성 완료 → {image_path}"
            )
        except Exception as e:
            results.append(
                f"⚠️ 페이지 {page.page_number}: 이미지 생성 실패 - {e}"
            )

    # 결과를 State에 저장
    tool_context.state["illustration_results"] = "\n".join(results)

    summary = f"📚 '{story.title}' 삽화 생성 완료!\n\n" + "\n".join(results)
    return summary


# ── Illustrator Agent ───────────────────────────────────────────────

illustrator = Agent(
    name="illustrator",
    model="gemini-3.0-flash",
    instruction="""당신은 어린이 동화 삽화가입니다.
generate_illustrations 도구를 호출하여 동화의 각 페이지에 대한 삽화를 생성하세요.
도구 호출 후 결과를 사용자에게 보기 좋게 정리하여 보여주세요.

결과 형식:
1. 동화 제목
2. 각 페이지별 본문과 삽화 생성 결과
3. 저장된 파일 경로""",
    tools=[generate_illustrations],
)


# ── Root Agent (Sequential) ─────────────────────────────────────────

root_agent = SequentialAgent(
    name="storyteller_pipeline",
    description="테마를 받아 어린이 동화를 작성하고 삽화를 생성하는 파이프라인",
    sub_agents=[story_writer, illustrator],
)
