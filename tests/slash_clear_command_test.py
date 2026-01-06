import pytest

pytestmark = pytest.mark.asyncio

from simple_agent.application.persisted_messages import PersistedMessages
from simple_agent.application.events import (
    SessionClearedEvent,
    UserPromptRequestedEvent,
)
from tests.session_storage_stub import SessionStorageStub
from tests.session_test_bed import SessionTestBed


async def test_slash_clear_command_in_full_session():
    session = (
        SessionTestBed()
        .with_llm_responses(["Response", "Response after clear"])
        .with_user_inputs("Initial message", "/clear", "After clear")
    )

    result = await session.run()

    result.events.assert_occured(UserPromptRequestedEvent, times=3)
    assert "user: After clear" in result.saved_messages
    assert "assistant: Response after clear" in result.saved_messages
    assert "Initial message" not in result.saved_messages, (
        "Messages before /clear should be cleared"
    )
    result.events.assert_occured(SessionClearedEvent, times=1)


async def test_consecutive_clear_commands():
    session = (
        SessionTestBed()
        .with_llm_responses(["Response after clears"])
        .with_user_inputs("Initial message", "/clear", "/clear", "After clears")
    )

    result = await session.run()

    result.events.assert_occured(UserPromptRequestedEvent, times=4)
    result.events.assert_occured(SessionClearedEvent, times=2)
    assert "/clear" not in result.saved_messages, "/clear should not be sent to LLM"
    assert "After clears" in result.saved_messages


async def test_agent_handles_slash_clear_command():
    session_storage = SessionStorageStub()
    messages = PersistedMessages(
        session_storage, system_prompt="You are a helpful assistant."
    )
    messages.user_says("Hello agent")
    messages.assistant_says("Hello! How can I help?")

    messages.clear()

    assert len(messages.to_list()) == 1, "Only system prompt should remain"
    assert messages.to_list()[0]["role"] == "system", (
        "System prompt should be preserved"
    )
    assert messages.to_list()[0]["content"] == "You are a helpful assistant."
    assert session_storage.saved == "system: You are a helpful assistant."
