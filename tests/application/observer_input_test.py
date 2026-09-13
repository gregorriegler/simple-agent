import asyncio

import pytest

from simple_agent.application.observer_input import ObserverInput
from simple_agent.application.queued_user_input import QueuedUserInput

pytestmark = pytest.mark.asyncio


def silent_observer_input() -> ObserverInput:
    return ObserverInput(QueuedUserInput())


async def test_reads_what_was_submitted():
    observer_input = silent_observer_input()

    observer_input.submit("a packet")

    assert await observer_input.read_async() == "a packet"


async def test_waits_for_the_next_packet():
    observer_input = silent_observer_input()

    reading = asyncio.ensure_future(observer_input.read_async())
    await asyncio.sleep(0)
    assert not reading.done()

    observer_input.submit("a later packet")

    assert await reading == "a later packet"


async def test_closing_ends_the_reading():
    observer_input = silent_observer_input()

    observer_input.close()

    assert await observer_input.read_async() == ""


async def test_reads_only_the_latest_packet():
    observer_input = silent_observer_input()

    observer_input.submit("packet 1")
    observer_input.submit("packet 2")

    assert await observer_input.read_async() == "packet 2"


async def test_reads_a_pending_packet_before_closing():
    observer_input = silent_observer_input()

    observer_input.submit("packet 1")
    observer_input.close()

    assert await observer_input.read_async() == "packet 1"
    assert await observer_input.read_async() == ""


async def test_reads_what_the_user_types_while_no_packet_arrives():
    user_input = QueuedUserInput()
    observer_input = ObserverInput(user_input)

    reading = asyncio.ensure_future(observer_input.read_async())
    await asyncio.sleep(0)
    user_input.submit_input("leave the name alone")

    assert await reading == "leave the name alone"


async def test_a_packet_is_kept_for_later_when_the_user_typed_first():
    user_input = QueuedUserInput()
    observer_input = ObserverInput(user_input)
    user_input.submit_input("typed")
    observer_input.submit("a packet")

    first = await observer_input.read_async()
    second = await observer_input.read_async()

    assert {first, second} == {"typed", "a packet"}
