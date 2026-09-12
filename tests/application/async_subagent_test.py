import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentFinishedEvent,
    UserPromptRequestedEvent,
)
from simple_agent.application.llm_stub import create_llm_stub
from tests.session_test_bed import SessionTestBed
from tests.tool_calls import complete_task, subagent

pytestmark = pytest.mark.asyncio


async def test_async_subagent_finishes_on_complete_task_without_asking_for_input():
    subagent_id = AgentId("Agent/Coding")
    llm = create_llm_stub(
        [
            subagent("coding", "do the sub task", background=True),
            "parent carries on",
            complete_task("sub done"),
        ]
    )

    result = await SessionTestBed().with_llm(llm).run()

    result.assert_event_occured(AgentFinishedEvent(subagent_id))
    asked = [
        e
        for e in result.events.get_all_events()
        if isinstance(e, UserPromptRequestedEvent) and e.agent_id == subagent_id
    ]
    assert asked == []
