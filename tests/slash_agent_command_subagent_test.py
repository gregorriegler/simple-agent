import pytest

from simple_agent.application.events import AgentStartedEvent
from tests.event_spy import EventSpy
from tests.session_test_bed import SessionTestBed

pytestmark = pytest.mark.asyncio


async def test_slash_agent_command_switches_subagent():
    spy = EventSpy()
    session = (
        SessionTestBed()
        .with_user_inputs("Start", "/agent orchestrator", "Hello", "/exit")
        .with_llm_responses(
            [
                "🛠️[subagent coding Do work]",  # 1. Main Agent spawns coding
                "Ready",  # 2. Coding agent responds to "Do work"
                "I am orchestrator",  # 3. Orchestrator responds to "Hello"
            ]
        )
        .on_event(AgentStartedEvent, spy.record_event)
    )

    await session.run()

    agent_started_events = [e for e in spy.events if isinstance(e, AgentStartedEvent)]

    subagent_starts = [e for e in agent_started_events if e.agent_name != "Agent"]

    assert len(subagent_starts) >= 2
    assert subagent_starts[0].agent_name == "Coding"
    assert subagent_starts[1].agent_name == "Orchestrator"
