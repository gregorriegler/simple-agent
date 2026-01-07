import pytest

from simple_agent.application.events import AgentChangedEvent
from tests.event_spy import EventSpy
from tests.session_test_bed import SessionTestBed

pytestmark = pytest.mark.asyncio


async def test_slash_agent_command_switches_agent():
    spy = EventSpy()
    session = (
        SessionTestBed()
        .with_user_inputs("Initial message", "/agent coding", "Message with new agent")
        .with_llm_responses(["Response 1", "Response 2"])
        .on_event(AgentChangedEvent, spy.record_event)
    )

    await session.run()

    agent_changed_events = [e for e in spy.events if isinstance(e, AgentChangedEvent)]
    assert len(agent_changed_events) == 1

    event = agent_changed_events[0]
    assert event.agent_definition is not None
    assert event.agent_definition.agent_name() == "Coding"
