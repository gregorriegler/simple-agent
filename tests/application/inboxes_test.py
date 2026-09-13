import asyncio

import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.inbox import Inbox
from simple_agent.application.inboxes import AgentInboxes

pytestmark = pytest.mark.asyncio

PARENT = AgentId("Agent")
CHILD = AgentId("Agent/Coding")


async def test_a_message_reaches_only_the_agent_it_was_sent_to():
    inboxes = AgentInboxes()

    inboxes.submit_input(CHILD, "hello child")

    assert inboxes.for_agent(PARENT).is_empty()
    assert inboxes.for_agent(CHILD).take() == "hello child"


async def test_the_same_agent_always_gets_the_same_inbox():
    inboxes = AgentInboxes()

    assert inboxes.for_agent(PARENT) is inboxes.for_agent(PARENT)


async def test_an_agent_may_bring_its_own_inbox():
    inboxes = AgentInboxes()
    own = Inbox()

    inboxes.assign(CHILD, own)
    inboxes.submit_input(CHILD, "hello")

    assert inboxes.for_agent(CHILD) is own
    assert own.take() == "hello"


async def test_closing_ends_every_inbox_including_later_ones():
    inboxes = AgentInboxes()
    parent = inboxes.for_agent(PARENT)

    inboxes.close()

    await asyncio.wait_for(parent.wait(), timeout=1)
    assert parent.take() == ""
    assert inboxes.for_agent(CHILD).take() == ""
