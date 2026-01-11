import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    UserPromptedEvent,
)
from simple_agent.infrastructure.file_event_store import FileEventStore
from tests.session_test_bed import SessionTestBed


@pytest.mark.asyncio
async def test_continuing_session_replays_finished_subagent_start_event(tmp_path):
    """
    When continuing a session, even finished subagents should have their
    AgentStartedEvent replayed so they show up in the UI.
    """
    parent_id = AgentId("Agent")
    subagent_id = AgentId("Agent/Sub")

    event_store = FileEventStore(tmp_path)
    # Root agent
    event_store.persist(
        AgentStartedEvent(agent_id=parent_id, agent_name="Agent", model="test-model")
    )
    event_store.persist(UserPromptedEvent(agent_id=parent_id, input_text="Start sub"))
    event_store.persist(
        AssistantRespondedEvent(
            agent_id=parent_id, response="🛠️[subagent coding Do it /]"
        )
    )

    # Subagent
    event_store.persist(
        AgentStartedEvent(
            agent_id=subagent_id,
            agent_name="Sub",
            model="test-model",
            agent_type="coding",
        )
    )
    event_store.persist(
        AssistantRespondedEvent(agent_id=subagent_id, response="I am done")
    )
    event_store.persist(AgentFinishedEvent(agent_id=subagent_id))

    captured_events = []

    def capture_event(event):
        captured_events.append(event)

    await (
        SessionTestBed()
        .with_event_store(event_store)
        .with_llm_responses(["Final response"])
        .continuing_session()
        .with_user_inputs("Finish")
        .on_event(AgentStartedEvent, capture_event)
        .run()
    )

    started_agent_ids = [
        e.agent_id for e in captured_events if isinstance(e, AgentStartedEvent)
    ]
    assert parent_id in started_agent_ids
    assert subagent_id in started_agent_ids, (
        "Finished subagent should also have its AgentStartedEvent replayed"
    )
