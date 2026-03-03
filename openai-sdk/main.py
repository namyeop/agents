import dotenv

dotenv.load_dotenv()

import streamlit as st
import asyncio
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

st.title("Agent Interface")

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Test Agent",
        instructions="""
        You are a helpful assistant.
        
        You have access to a web search tool to look up information.
        Use it when you need to find current information or verify facts.
        """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                vector_store_ids=["my_vector_store"],
                max_num_results=3,
            ),
        ],
    )

agent = st.session_state["agent"]

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(":memory:", "chat-memory.db")

session = st.session_state["session"]


async def load_messages():
    messages = await session.get_items()

    for message in messages:
        role = "user" if message.get("role") == "user" else "assistant"
        if role == "user":
            with st.chat_message("user"):
                st.write(message.get("content"))
        else:
            with st.chat_message("assistant"):
                if "content" in message:
                    st.write(message["content"][0]["text"])


asyncio.run(load_messages())


async def run_agent(prompt):
    with st.chat_message("assistant"):
        text_placeholder = st.empty()
        response = ""

        stream = Runner.run_streamed(agent, prompt, session=session)
        async for message in stream.stream_events():
            if message.type == "raw_response_event":
                if message.data.type == "response.output_text.delta":
                    response += message.data.delta
                    text_placeholder.write(response)


prompt = st.chat_input(
    "Enter your message here...",
    file_type=["txt", "pdf"],
    accept_file=True,
)

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))

with st.sidebar:
    reset = st.button("Reset Chat")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
