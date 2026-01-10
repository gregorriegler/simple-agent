import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.llm import Messages
from simple_agent.infrastructure.file_session_storage import FileSessionStorage
from tests.session_test_bed import CapturingLLM, SessionTestBed


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

    assert capturing_llm.first_call_contained("user", "Hello")
    assert capturing_llm.first_call_contained("assistant", "Hi there!")


def _messages_with(raw_messages: list[dict]) -> Messages:
    return Messages(raw_messages)
