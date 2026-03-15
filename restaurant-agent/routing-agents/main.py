import asyncio
import os
import streamlit as st

import dotenv

from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)
from models import RestaurantContext
from my_agents.triage_agent import triage_agent

AGENT_DISPLAY_NAMES = {
    "Menu Agent": "🍽️ 메뉴 전문가",
    "Order Agent": "📝 주문 전문가",
    "Reservation Agent": "📅 예약 전문가",
    "Triage Agent": "👋 안내 데스크",
    "Complaints Agent": "😔 불만 처리 전문가",
}

st.set_page_config(page_title="Nomad Kitchen", page_icon="🍽️")

restaurant_ctx = RestaurantContext(
    customer_id=1,
    name="guest",
)


def configure_api_key() -> None:
    dotenv.load_dotenv()

    secret_api_key = None
    try:
        secret_api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret_api_key = None

    if secret_api_key and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = secret_api_key


configure_api_key()

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "restaurant-chat",
        "restaurant-memory.db",
    )
session = st.session_state["session"]

if "transcript" not in st.session_state:
    st.session_state["transcript"] = []
if "active_agent_name" not in st.session_state:
    st.session_state["active_agent_name"] = AGENT_DISPLAY_NAMES["Triage Agent"]


st.title("🍽️ Nomad Kitchen")
st.caption("Korean-Italian Fusion Restaurant Bot")


async def paint_history():
    if not st.session_state["transcript"]:
        messages = await session.get_items()
        hydrated_transcript = []
        for message in messages:
            if "role" not in message:
                continue

            if message["role"] == "user":
                hydrated_transcript.append(
                    {"role": "human", "content": message["content"]}
                )
            elif message.get("type") == "message":
                hydrated_transcript.append(
                    {
                        "role": "ai",
                        "content": message["content"][0]["text"],
                        "agent_name": AGENT_DISPLAY_NAMES["Triage Agent"],
                    }
                )

        st.session_state["transcript"] = hydrated_transcript

    for entry in st.session_state["transcript"]:
        with st.chat_message(entry["role"]):
            if entry["role"] == "ai" and entry.get("agent_name"):
                st.caption(f"응답 에이전트: {entry['agent_name']}")
            st.write(entry["content"].replace("$", r"\$"))


asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        agent_placeholder = st.empty()
        text_placeholder = st.empty()
        handoff_placeholder = st.empty()
        response = ""
        active_agent_name = AGENT_DISPLAY_NAMES["Triage Agent"]

        agent_placeholder.caption(f"응답 에이전트: {active_agent_name}")
        st.session_state["text_placeholder"] = text_placeholder
        st.session_state["handoff_placeholder"] = handoff_placeholder

        stream = Runner.run_streamed(
            triage_agent,
            message,
            session=session,
            context=restaurant_ctx,
        )

        async for event in stream.stream_events():
            if event.type == "agent_updated_stream_event":
                agent_name = event.new_agent.name
                display_name = AGENT_DISPLAY_NAMES.get(agent_name, agent_name)
                active_agent_name = display_name
                st.session_state["active_agent_name"] = display_name
                agent_placeholder.caption(f"응답 에이전트: {display_name}")
                handoff_placeholder.info(
                    f"{display_name}에게 연결합니다..."
                )

            elif event.type == "raw_response_event":
                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response.replace("$", r"\$"))

        handoff_placeholder.empty()
        st.session_state["transcript"].append(
            {
                "role": "ai",
                "content": response,
                "agent_name": active_agent_name,
            }
        )


GUARDRAIL_MESSAGES = {
    "input": "죄송합니다. 레스토랑과 관련된 질문만 도와드릴 수 있습니다. 메뉴, 주문, 예약 또는 불만 사항에 대해 문의해 주세요.",
    "output": "죄송합니다. 응답을 처리하는 중 문제가 발생했습니다. 다시 질문해 주시겠어요?",
}

message = st.chat_input("무엇을 도와드릴까요? (메뉴, 주문, 예약)")

if message:
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()
    if "handoff_placeholder" in st.session_state:
        st.session_state["handoff_placeholder"].empty()

    with st.chat_message("human"):
        st.write(message)
    st.session_state["transcript"].append({"role": "human", "content": message})
    try:
        asyncio.run(run_agent(message))
    except InputGuardrailTripwireTriggered:
        with st.chat_message("ai"):
            st.warning(GUARDRAIL_MESSAGES["input"])
        st.session_state["transcript"].append(
            {
                "role": "ai",
                "content": GUARDRAIL_MESSAGES["input"],
                "agent_name": "입력 가드레일",
            }
        )
    except OutputGuardrailTripwireTriggered:
        with st.chat_message("ai"):
            st.warning(GUARDRAIL_MESSAGES["output"])
        st.session_state["transcript"].append(
            {
                "role": "ai",
                "content": GUARDRAIL_MESSAGES["output"],
                "agent_name": "출력 가드레일",
            }
        )


with st.sidebar:
    st.header("⚙️ 설정")
    st.info(f"현재 응답 에이전트: {st.session_state['active_agent_name']}")
    reset = st.button("🗑️ 대화 초기화")
    if reset:
        asyncio.run(session.clear_session())
        st.session_state["transcript"] = []
        st.session_state["active_agent_name"] = AGENT_DISPLAY_NAMES["Triage Agent"]
        st.rerun()
