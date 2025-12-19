import pytest
from simple_agent.application.input import Input


pytestmark = pytest.mark.asyncio

class UserInputStub:
    def __init__(self, value="input"):
        self.value = value
        self.calls = 0

    async def read_async(self):
        self.calls += 1
        return self.value

    def escape_requested(self):
        return False


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


async def test_multiple_stacked_messages_returned_in_lifo_order():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)
    feed.stack("first")
    feed.stack("second")
    feed.stack("third")

    assert await feed.read_async() == "third"
    assert await feed.read_async() == "second"
    assert await feed.read_async() == "first"
    assert user_input_port.calls == 0


async def test_has_stacked_messages_returns_correct_boolean():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)

    assert feed.has_stacked_messages() == False

    feed.stack("message")
    assert feed.has_stacked_messages() == True

    await feed.read_async()
    assert feed.has_stacked_messages() == False


async def test_mixing_stacked_and_user_input_reads():
    user_input_port = UserInputStub("user input")
    feed = Input(user_input_port)
    feed.stack("stacked1")
    feed.stack("stacked2")

    assert await feed.read_async() == "stacked2"
    assert user_input_port.calls == 0

    assert await feed.read_async() == "stacked1"
    assert user_input_port.calls == 0

    assert await feed.read_async() == "user input"
    assert user_input_port.calls == 1

    assert await feed.read_async() == "user input"
    assert user_input_port.calls == 2
