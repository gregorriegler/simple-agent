import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
    SessionClearedEvent,
    SessionEndedEvent,
    UserPromptRequestedEvent,
)
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
    messages = result.current_messages(AgentId("Agent"))
    assert "user: After clear" in messages
    assert "assistant: Response after clear" in messages
    assert "Initial message" not in messages, "Messages before /clear should be cleared"
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
    messages = result.current_messages(AgentId("Agent"))
    assert "/clear" not in messages, "/clear should not be sent to LLM"
    assert "After clears" in messages


async def test_agent_handles_slash_clear_command():
    from simple_agent.application.llm import Messages

    messages = Messages(system_prompt="You are a helpful assistant.")
    messages.user_says("Hello agent")
    messages.assistant_says("Hello! How can I help?")

    messages.clear()

    assert len(messages.to_list()) == 1, "Only system prompt should remain"
    assert messages.to_list()[0]["role"] == "system", (
        "System prompt should be preserved"
    )
    assert messages.to_list()[0]["content"] == "You are a helpful assistant."


async def test_slash_clear_command_closes_open_observers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    session = (
        SessionTestBed()
        .observed_by(["naming"], "diff --git a/greeting.txt b/greeting.txt\n+Hello")
        .with_user_inputs("Store greeting", "/clear", "After clear")
        .with_llm_responses(
            [
                "🛠️[create-file greeting.txt]\nHello\n🛠️[/end]",
                "Response after clear",
            ]
        )
        .with_observer_responses(["🛠️[complete-task looks good /]"])
    )

    result = await session.run()

    observer_id = AgentId("Agent/Naming")
    result.events.assert_event_occured(SessionClearedEvent(AgentId("Agent")), times=1)
    result.events.assert_event_occured(SessionEndedEvent(observer_id), times=1)
    result.events.assert_event_occured(AgentFinishedEvent(observer_id), times=1)
