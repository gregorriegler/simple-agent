import asyncio

import pytest

from simple_agent.application.input import Input

pytestmark = pytest.mark.asyncio


class UserInputStub:
    def __init__(self, value="input", pending=None):
        self.value = value
        self.calls = 0
        self.pending = list(pending) if pending else []

    async def read_async(self):
        self.calls += 1
        return self.value

    def escape_requested(self):
        return False

    def close(self) -> None:
        pass

    def drain(self):
        pending, self.pending = self.pending, []
        return pending


async def test_input_uses_display_input_when_stack_empty():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)

    result = await feed.read_async()

    assert result == "user input"
    assert user_input_port.calls == 1


async def test_input_returns_stacked_message_before_display():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)
    feed.stack("stacked")

    result = await feed.read_async()

    assert result == "stacked"
    assert user_input_port.calls == 0


async def test_multiple_stacked_messages_returned_in_fifo_order():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)
    feed.stack("first")
    feed.stack("second")
    feed.stack("third")

    assert await feed.read_async() == "first"
    assert await feed.read_async() == "second"
    assert await feed.read_async() == "third"
    assert user_input_port.calls == 0


async def test_has_stacked_messages_returns_correct_boolean():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)

    assert not feed.has_stacked_messages()

    feed.stack("message")
    assert feed.has_stacked_messages()

    await feed.read_async()
    assert not feed.has_stacked_messages()


async def test_mixing_stacked_and_user_input_reads():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)
    feed.stack("stacked1")
    feed.stack("stacked2")

    assert await feed.read_async() == "stacked1"
    assert user_input_port.calls == 0

    assert await feed.read_async() == "stacked2"
    assert user_input_port.calls == 0

    assert await feed.read_async() == "user input"
    assert user_input_port.calls == 1

    assert await feed.read_async() == "user input"
    assert user_input_port.calls == 2


async def test_drain_returns_stacked_and_pending_messages_in_fifo_order():
    user_input_port = UserInputStub("user input", pending=["typed while working"])
    feed = Input(user_input_port)
    feed.stack("stacked")

    assert feed.drain() == ["stacked", "typed while working"]


async def test_drain_empties_the_queue():
    user_input_port = UserInputStub("user input", pending=["typed"])
    feed = Input(user_input_port)
    feed.stack("stacked")

    feed.drain()

    assert feed.drain() == []
    assert not feed.has_stacked_messages()


class BlockingUserInput(UserInputStub):
    async def read_async(self):
        self.calls += 1
        await asyncio.Event().wait()
        return "never"


async def test_message_stacked_while_waiting_on_the_user_is_read_at_once():
    feed = Input(BlockingUserInput())
    reading = asyncio.create_task(feed.read_async())
    await asyncio.sleep(0)

    feed.stack("from a subagent")

    assert await asyncio.wait_for(reading, timeout=1) == "from a subagent"


async def test_a_message_typed_as_the_read_is_cancelled_is_kept_for_the_next_read():
    feed = Input(UserInputStub("typed"))
    reading = asyncio.create_task(feed.read_async())
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    reading.cancel()
    with pytest.raises(asyncio.CancelledError):
        await reading

    assert feed.drain() == ["typed"]
