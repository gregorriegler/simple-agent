import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    SessionClearedEvent,
    UserPromptRequestedEvent,
)
from simple_agent.application.persisted_messages import PersistedMessages
from tests.session_storage_stub import SessionStorageStub
from tests.session_test_bed import SessionTestBed

pytestmark = pytest.mark.asyncio


async def test_slash_clear_command_in_full_session():
    session = (
        SessionTestBed()
        .with_llm_responses(["Response", "Response after clear"])
        .with_user_inputs("Initial message", "/clear", "After clear")
    )

    result = await session.run()

    result.events.assert_occured(UserPromptRequestedEvent, times=3)
    saved = result.saved_messages.get("Agent", "")
    assert "user: After clear" in saved
    assert "assistant: Response after clear" in saved
    assert "Initial message" not in saved, "Messages before /clear should be cleared"
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
    saved = result.saved_messages.get("Agent", "")
    assert "/clear" not in saved, "/clear should not be sent to LLM"
    assert "After clears" in saved


async def test_agent_handles_slash_clear_command():
    session_storage = SessionStorageStub()
    messages = PersistedMessages(
        session_storage,
        agent_id=AgentId("Agent"),
        system_prompt="You are a helpful assistant.",
    )
    messages.user_says("Hello agent")
    messages.assistant_says("Hello! How can I help?")

    messages.clear()

    assert len(messages.to_list()) == 1, "Only system prompt should remain"
    assert messages.to_list()[0]["role"] == "system", (
        "System prompt should be preserved"
    )
    assert messages.to_list()[0]["content"] == "You are a helpful assistant."
    assert session_storage.saved["Agent"] == "system: You are a helpful assistant."
