import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.non_interactive_inboxes import NonInteractiveInboxes

pytestmark = pytest.mark.asyncio


async def test_an_agent_reads_what_it_was_given_and_then_ends():
    inbox = NonInteractiveInboxes().for_agent(AgentId("Agent"))
    inbox.put("the task")

    assert inbox.take() == "the task"
    assert inbox.take() == ""
