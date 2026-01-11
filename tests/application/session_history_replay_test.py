import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    UserPromptedEvent,
)
from simple_agent.infrastructure.file_event_store import FileEventStore
from tests.session_test_bed import SessionTestBed


@pytest.mark.asyncio
async def test_continuing_session_replays_user_messages_as_events(tmp_path):
    """When continuing a session, previously sent user messages should be replayed as UserPromptedEvents."""
    agent_id = AgentId("Agent")
    event_store = FileEventStore(tmp_path)
    event_store.persist(
        UserPromptedEvent(agent_id=agent_id, input_text="Hello from the past")
    )
    event_store.persist(
        AssistantRespondedEvent(agent_id=agent_id, response="Hi there!")
    )

    result = await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue please")
        .run()
    )

    # The historical user message should be replayed as an event
    result.assert_event_occured(
        UserPromptedEvent(agent_id=agent_id, input_text="Hello from the past")
    )


@pytest.mark.asyncio
async def test_continuing_session_replays_assistant_messages_as_events(tmp_path):
    """When continuing a session, previous assistant messages should be replayed as AssistantSaidEvents."""
    agent_id = AgentId("Agent")
    event_store = FileEventStore(tmp_path)
    event_store.persist(UserPromptedEvent(agent_id=agent_id, input_text="Hello"))
    event_store.persist(
        AssistantRespondedEvent(
            agent_id=agent_id, response="Previous response from assistant"
        )
    )

    result = await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    # The historical assistant message should be replayed as an event
    result.assert_event_occured(
        AssistantSaidEvent(
            agent_id=agent_id, message="Previous response from assistant"
        )
    )


@pytest.mark.asyncio
async def test_continuing_session_replays_subagent_history(tmp_path):
    """When continuing a session with subagents, their history should also be replayed."""
    parent_id = AgentId("Agent")
    subagent_id = AgentId("Agent/Coding")

    event_store = FileEventStore(tmp_path)
    event_store.persist(UserPromptedEvent(agent_id=parent_id, input_text="Parent task"))
    event_store.persist(
        AssistantRespondedEvent(
            agent_id=parent_id,
            response="Starting subagent\n🛠️[subagent coding Do the task /]",
        )
    )
    event_store.persist(
        AgentStartedEvent(agent_id=subagent_id, agent_name="Coding", model="test-model")
    )
    event_store.persist(
        UserPromptedEvent(agent_id=subagent_id, input_text="Subagent task")
    )
    event_store.persist(
        AssistantRespondedEvent(agent_id=subagent_id, response="Subagent response")
    )

    result = await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    # Subagent should be started
    result.assert_event_occured(
        AgentStartedEvent(agent_id=subagent_id, agent_name="Coding", model="test-model")
    )
    # Subagent's historical messages should be replayed
    result.assert_event_occured(
        UserPromptedEvent(agent_id=subagent_id, input_text="Subagent task")
    )
    result.assert_event_occured(
        AssistantSaidEvent(agent_id=subagent_id, message="Subagent response")
    )


@pytest.mark.asyncio
async def test_continuing_session_restores_token_metadata(tmp_path):
    """When continuing a session, token usage display should be restored."""
    agent_id = AgentId("Agent")
    event_store = FileEventStore(tmp_path)
    event_store.persist(UserPromptedEvent(agent_id=agent_id, input_text="Hello"))
    event_store.persist(
        AssistantRespondedEvent(
            agent_id=agent_id,
            response="Hi there!",
            model="claude-3-sonnet",
            token_usage_display="0.8%",
        )
    )

    result = await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue")
        .run()
    )

    # Token metadata should be restored
    # In the new implementation, AssistantRespondedEvent is replayed as AssistantSaidEvent
    # but the original AssistantRespondedEvent is also replayed.
    result.assert_event_occured(
        AssistantRespondedEvent(
            agent_id=agent_id,
            response="Hi there!",
            model="claude-3-sonnet",
            token_usage_display="0.8%",
        )
    )
