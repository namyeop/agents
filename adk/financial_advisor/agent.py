import logging
from functools import lru_cache
from typing import Optional

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from openai import OpenAI
from openai import OpenAIError

LOGGER = logging.getLogger(__name__)

MODEL = LiteLlm(model="", temperature=1)


def get_weather(location: str) -> str:
    return f"The current weather in {location} is sunny with a temperature of 25°C."


agent = Agent(
    name="weather_agent",
    instruction="사용자와 한국어로 대화를 나눕니다.",
    model="",
    tools=[
        get_weather,
    ],
)

root_agent = agent
