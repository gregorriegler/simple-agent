import pytest

from simple_agent.application.queued_user_input import QueuedUserInput

pytestmark = pytest.mark.asyncio


async def test_queued_input_hands_out_submitted_messages_in_order():
    user_input = QueuedUserInput()
    user_input.submit_input("hello")
    user_input.submit_input("world")

    assert await user_input.read_async() == "hello"
    assert await user_input.read_async() == "world"
