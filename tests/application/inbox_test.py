import asyncio

import pytest

from simple_agent.application.inbox import Inbox

pytestmark = pytest.mark.asyncio


def test_new_inbox_is_empty():
    assert Inbox().is_empty()


def test_put_message_makes_inbox_non_empty():
    inbox = Inbox()

    inbox.put("hello")

    assert not inbox.is_empty()


def test_take_returns_messages_in_the_order_they_arrived():
    inbox = Inbox()
    inbox.put("first")
    inbox.put("second")

    assert inbox.take() == "first"
    assert inbox.take() == "second"
    assert inbox.is_empty()


def test_drain_returns_all_messages_oldest_first_and_empties_inbox():
    inbox = Inbox()
    inbox.put("first")
    inbox.put("second")

    assert inbox.drain() == ["first", "second"]
    assert inbox.is_empty()


async def test_a_closed_inbox_hands_out_its_messages_and_then_an_empty_prompt():
    inbox = Inbox()
    inbox.put("last words")

    inbox.close()

    assert inbox.take() == "last words"
    assert inbox.take() == ""
    assert inbox.take() == ""


async def test_waiting_on_a_closed_inbox_returns_at_once():
    inbox = Inbox()

    inbox.close()

    await asyncio.wait_for(inbox.wait(), timeout=1)


async def test_waiting_returns_once_a_message_arrives():
    inbox = Inbox()
    waiting = asyncio.ensure_future(inbox.wait())
    await asyncio.sleep(0)
    assert not waiting.done()

    inbox.put("hello")

    await asyncio.wait_for(waiting, timeout=1)
