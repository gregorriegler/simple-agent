import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.routed_user_input import RoutedUserInput

pytestmark = pytest.mark.asyncio

PARENT = AgentId("Agent")
CHILD = AgentId("Agent/Coding")


async def test_a_message_reaches_only_the_agent_it_was_sent_to():
    router = RoutedUserInput()

    router.submit_input(CHILD, "hello child")

    assert router.for_agent(PARENT).drain() == []
    assert await router.for_agent(CHILD).read_async() == "hello child"


async def test_the_same_agent_always_gets_the_same_channel():
    router = RoutedUserInput()

    assert router.for_agent(PARENT) is router.for_agent(PARENT)


async def test_closing_ends_every_channel_including_later_ones():
    router = RoutedUserInput()
    parent = router.for_agent(PARENT)

    router.close()

    assert await parent.read_async() == ""
    assert await router.for_agent(CHILD).read_async() == ""
