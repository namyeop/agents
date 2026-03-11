import dotenv

dotenv.load_dotenv()

import asyncio
import streamlit as st
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered, Runner, SQLiteSession
from models import RestaurantContext
from my_agents.triage_agent import triage_agent

AGENT_DISPLAY_NAMES = {
    "Menu Agent": "🍽️ 메뉴 전문가",
    "Order Agent": "📝 주문 전문가",
    "Reservation Agent": "📅 예약 전문가",
    "Triage Agent": "👋 안내 데스크",
    "Complaints Agent": "😔 불만 처리 전문가",
}

restaurant_ctx = RestaurantContext(
    customer_id=1,
    name="nico",
)

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "restaurant-chat",
        "restaurant-memory.db",
    )
session = st.session_state["session"]


st.set_page_config(page_title="Nico's Kitchen", page_icon="🍽️")
st.title("🍽️ Nico's Kitchen")
st.caption("Korean-Italian Fusion Restaurant Bot")


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            if message["role"] == "user":
                with st.chat_message("human"):
                    st.write(message["content"])
            elif message["type"] == "message":
                with st.chat_message("ai"):
                    st.write(message["content"][0]["text"].replace("$", r"\$"))


asyncio.run(paint_history())


async def run_agent(message):
    with st.chat_message("ai"):
        text_placeholder = st.empty()
        handoff_placeholder = st.empty()
        response = ""

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
                handoff_placeholder.info(
                    f"{display_name}에게 연결합니다..."
                )

            elif event.type == "raw_response_event":
                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response.replace("$", r"\$"))

        handoff_placeholder.empty()


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
    try:
        asyncio.run(run_agent(message))
    except InputGuardrailTripwireTriggered:
        with st.chat_message("ai"):
            st.warning(GUARDRAIL_MESSAGES["input"])
    except OutputGuardrailTripwireTriggered:
        with st.chat_message("ai"):
            st.warning(GUARDRAIL_MESSAGES["output"])


with st.sidebar:
    st.header("⚙️ 설정")
    reset = st.button("🗑️ 대화 초기화")
    if reset:
        asyncio.run(session.clear_session())
        st.rerun()
