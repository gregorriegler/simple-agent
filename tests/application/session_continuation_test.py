import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.llm import (
    ChatMessages,
    LLMResponse,
    Messages,
    TokenUsage,
)
from simple_agent.infrastructure.file_session_storage import FileSessionStorage
from tests.session_test_bed import SessionTestBed


class CapturingLLM:
    def __init__(self):
        self.captured_messages: list[ChatMessages] = []

    @property
    def model(self) -> str:
        return "capturing-model"

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        self.captured_messages.append(list(messages))
        return LLMResponse(
            content="Done",
            model=self.model,
            usage=TokenUsage(0, 0, 0),
        )


@pytest.mark.asyncio
async def test_continued_session_loads_previous_messages_into_llm(tmp_path):
    agent_id = AgentId("Agent")

    storage = FileSessionStorage.create(tmp_path, continue_session=False, cwd=tmp_path)
    storage.save_messages(
        agent_id,
        _messages_with(
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        ),
    )

    continued_storage = FileSessionStorage.create(
        tmp_path, continue_session=True, cwd=tmp_path
    )

    capturing_llm = CapturingLLM()

    await (
        SessionTestBed()
        .with_session_storage(continued_storage)
        .with_llm(capturing_llm)
        .continuing_session()
        .with_user_inputs("Continue please")
        .run()
    )

    assert len(capturing_llm.captured_messages) >= 1
    first_call_messages = capturing_llm.captured_messages[0]

    user_messages = [m["content"] for m in first_call_messages if m["role"] == "user"]
    assistant_messages = [
        m["content"] for m in first_call_messages if m["role"] == "assistant"
    ]

    assert "Hello" in user_messages
    assert "Hi there!" in assistant_messages


def _messages_with(raw_messages: list[dict]) -> Messages:
    return Messages(raw_messages)
