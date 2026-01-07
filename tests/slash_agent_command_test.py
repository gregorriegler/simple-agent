import pytest

from simple_agent.application.events import AgentStartedEvent
from tests.event_spy import EventSpy
from tests.session_test_bed import SessionTestBed

pytestmark = pytest.mark.asyncio


async def test_slash_agent_command_switches_agent():
    spy = EventSpy()
    session = (
        SessionTestBed()
        .with_user_inputs("Initial message", "/agent coding", "Message with new agent")
        .with_llm_responses(["Response 1", "Response 2"])
        .on_event(AgentStartedEvent, spy.record_event)
    )

    await session.run()

    agent_started_events = [e for e in spy.events if isinstance(e, AgentStartedEvent)]
    assert len(agent_started_events) == 2

    assert agent_started_events[0].agent_name == "Agent"
    assert agent_started_events[1].agent_name == "Coding"
