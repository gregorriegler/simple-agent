import pytest

from simple_agent.application.events import AssistantThoughtEvent
from simple_agent.application.llm import TokenUsage
from simple_agent.application.text_response import emoji_response
from tests.session_test_bed import SessionTestBed

pytestmark = pytest.mark.asyncio


class ThinkingLLM:
    def __init__(self, turns: list[tuple[str, str]]):
        self._turns = list(turns)

    @property
    def model(self) -> str:
        return "thinking-model"

    async def call_async(self, messages):
        content, thought = self._turns.pop(0)
        return emoji_response(content, self.model, TokenUsage(), thought)


async def published_thoughts(turns: list[tuple[str, str]]) -> list[str]:
    thoughts: list[str] = []
    await (
        SessionTestBed()
        .with_llm(ThinkingLLM(turns))
        .with_user_inputs("Hello")
        .on_event(AssistantThoughtEvent, lambda event: thoughts.append(event.thought))
        .run()
    )
    return thoughts


async def test_the_agent_publishes_what_the_model_thought():
    turns = [("🛠️[complete-task done /]", "The user only wants a greeting.")]

    thoughts = await published_thoughts(turns)

    assert thoughts == ["The user only wants a greeting."]


async def test_a_turn_without_a_thought_publishes_nothing():
    turns = [("🛠️[complete-task done /]", "")]

    thoughts = await published_thoughts(turns)

    assert thoughts == []
