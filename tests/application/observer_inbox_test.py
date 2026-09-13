import asyncio

import pytest

from simple_agent.application.observer_inbox import ObserverInbox

pytestmark = pytest.mark.asyncio


async def test_hands_out_the_observed_packet():
    inbox = ObserverInbox()

    inbox.observe("a packet")

    assert inbox.take() == "a packet"


async def test_waits_for_the_next_packet():
    inbox = ObserverInbox()
    waiting = asyncio.ensure_future(inbox.wait())
    await asyncio.sleep(0)
    assert not waiting.done()

    inbox.observe("a later packet")

    await asyncio.wait_for(waiting, timeout=1)
    assert inbox.take() == "a later packet"


async def test_only_the_latest_packet_counts():
    inbox = ObserverInbox()

    inbox.observe("packet 1")
    inbox.observe("packet 2")

    assert inbox.take() == "packet 2"
    assert inbox.take() == ""


async def test_a_pending_packet_is_read_before_the_end_of_input():
    inbox = ObserverInbox()
    inbox.observe("packet 1")

    inbox.close()

    assert inbox.take() == "packet 1"
    assert inbox.take() == ""


async def test_what_the_user_typed_comes_before_the_pending_packet():
    inbox = ObserverInbox()
    inbox.observe("a packet")
    inbox.put("leave the name alone")

    assert inbox.take() == "leave the name alone"
    assert inbox.take() == "a packet"


async def test_a_packet_is_a_prompt_and_not_drained_mid_work():
    inbox = ObserverInbox()
    inbox.observe("a packet")
    inbox.put("typed")

    assert inbox.drain() == ["typed"]
    assert inbox.is_empty()
    assert inbox.take() == "a packet"
