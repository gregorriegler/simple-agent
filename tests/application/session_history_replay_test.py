import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
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

    result.assert_event_occured(
        AgentStartedEvent(agent_id=subagent_id, agent_name="Coding", model="test-model")
    )
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

    result.assert_event_occured(
        AssistantRespondedEvent(
            agent_id=agent_id,
            response="Hi there!",
            model="claude-3-sonnet",
            token_usage_display="0.8%",
        )
    )


@pytest.mark.asyncio
async def test_continuing_session_replays_agent_started_event_for_root_agent(tmp_path):
    """When continuing a session, the root agent's AgentStartedEvent should be replayed so the UI can create the tab."""
    agent_id = AgentId("Agent")
    event_store = FileEventStore(tmp_path)
    event_store.persist(
        AgentStartedEvent(agent_id=agent_id, agent_name="Agent", model="test-model")
    )
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

    result.assert_event_occured(
        AgentStartedEvent(agent_id=agent_id, agent_name="Agent", model="test-model")
    )


@pytest.mark.asyncio
async def test_continuing_session_without_stored_agent_started_still_works(tmp_path):
    """
    When continuing a session that doesn't have AgentStartedEvent stored (e.g., old format),
    the HistoryReplayer synthesizes an AgentStartedEvent so the UI can create the tab.
    """
    agent_id = AgentId("Agent")
    event_store = FileEventStore(tmp_path)
    event_store.persist(
        UserPromptedEvent(agent_id=agent_id, input_text="Hello from the past")
    )
    event_store.persist(
        AssistantRespondedEvent(agent_id=agent_id, response="Hi there!")
    )

    events_in_order = []

    def capture_event(event):
        events_in_order.append(type(event).__name__)

    await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("Continue please")
        .on_event(AgentStartedEvent, capture_event)
        .on_event(UserPromptedEvent, capture_event)
        .on_event(AssistantSaidEvent, capture_event)
        .run()
    )

    user_prompted_indices = [
        i for i, e in enumerate(events_in_order) if e == "UserPromptedEvent"
    ]
    agent_started_indices = [
        i for i, e in enumerate(events_in_order) if e == "AgentStartedEvent"
    ]

    assert len(agent_started_indices) > 0, "AgentStartedEvent should occur"
    assert len(user_prompted_indices) > 0, "UserPromptedEvent should occur"

    first_agent_started = agent_started_indices[0]
    first_user_prompted = user_prompted_indices[0]

    assert first_agent_started < first_user_prompted, (
        f"AgentStartedEvent (index {first_agent_started}) should come before "
        f"UserPromptedEvent (index {first_user_prompted}). "
        f"Actual order: {events_in_order}"
    )


@pytest.mark.asyncio
async def test_continuing_finished_session_replays_agent_started_before_messages(
    tmp_path,
):
    """
    When continuing a session where the root agent has AgentFinishedEvent,
    the AgentStartedEvent should still be replayed so the UI can create the tab.
    This is the real-world scenario: user has a completed session and wants to continue.
    """
    agent_id = AgentId("Agent")
    event_store = FileEventStore(tmp_path)
    event_store.persist(
        AgentStartedEvent(agent_id=agent_id, agent_name="Agent", model="test-model")
    )
    event_store.persist(UserPromptedEvent(agent_id=agent_id, input_text="hi"))
    event_store.persist(
        AssistantRespondedEvent(agent_id=agent_id, response="Hello there!")
    )
    event_store.persist(AgentFinishedEvent(agent_id=agent_id))

    events_in_order = []

    def capture_event(event):
        events_in_order.append(type(event).__name__)

    await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses(["Done"])
        .continuing_session()
        .with_user_inputs("continue")
        .on_event(AgentStartedEvent, capture_event)
        .on_event(UserPromptedEvent, capture_event)
        .on_event(AssistantSaidEvent, capture_event)
        .run()
    )

    agent_started_idx = events_in_order.index("AgentStartedEvent")
    user_prompted_idx = events_in_order.index("UserPromptedEvent")

    assert agent_started_idx < user_prompted_idx, (
        f"AgentStartedEvent (index {agent_started_idx}) should come before "
        f"UserPromptedEvent (index {user_prompted_idx}). "
        f"Actual order: {events_in_order}"
    )
