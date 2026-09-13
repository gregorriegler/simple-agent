import asyncio

import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import AgentFinishedEvent
from simple_agent.application.inboxes import AgentInboxes
from tests.agent.agent_interrupts_immediately_test import SlowLLM
from tests.application.background_subagent_test import _factory
from tests.test_tool_library import FixedLLMProvider

pytestmark = pytest.mark.asyncio

PARENT = AgentId("Agent")
CHILD = AgentId("Agent/Coding")


async def test_interrupting_the_parent_ends_the_subagent_it_waits_for():
    event_bus = SimpleEventBus()
    finished: list[AgentFinishedEvent] = []
    event_bus.subscribe(AgentFinishedEvent, finished.append)
    factory = _factory(FixedLLMProvider(SlowLLM()), AgentInboxes(), event_bus)
    spawn = factory.create_spawner(PARENT, factory.create_inbox(PARENT))

    parent_waits = asyncio.create_task(spawn(AgentType("coding"), "do the sub task"))
    await asyncio.sleep(0.1)
    parent_waits.cancel()

    await asyncio.wait({parent_waits}, timeout=1)

    assert parent_waits.cancelled(), "the parent is still waiting for its subagent"
    assert [event.agent_id for event in finished] == [CHILD]
