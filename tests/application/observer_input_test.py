import asyncio

import pytest

from simple_agent.application.observer_input import ObserverInput

pytestmark = pytest.mark.asyncio


async def test_reads_what_was_submitted():
    observer_input = ObserverInput()

    observer_input.submit("a packet")

    assert await observer_input.read_async() == "a packet"


async def test_waits_for_the_next_packet():
    observer_input = ObserverInput()

    reading = asyncio.ensure_future(observer_input.read_async())
    await asyncio.sleep(0)
    assert not reading.done()

    observer_input.submit("a later packet")

    assert await reading == "a later packet"


async def test_closing_ends_the_reading():
    observer_input = ObserverInput()

    observer_input.close()

    assert await observer_input.read_async() == ""


async def test_reads_only_the_latest_packet():
    observer_input = ObserverInput()

    observer_input.submit("packet 1")
    observer_input.submit("packet 2")

    assert await observer_input.read_async() == "packet 2"


async def test_reads_a_pending_packet_before_closing():
    observer_input = ObserverInput()

    observer_input.submit("packet 1")
    observer_input.close()

    assert await observer_input.read_async() == "packet 1"
    assert await observer_input.read_async() == ""
