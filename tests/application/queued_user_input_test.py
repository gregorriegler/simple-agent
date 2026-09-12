import pytest

from simple_agent.application.queued_user_input import QueuedUserInput

pytestmark = pytest.mark.asyncio


async def test_queued_input_knows_when_a_message_is_pending():
    user_input = QueuedUserInput()
    assert user_input.has_pending() is False

    user_input.submit_input("hello")

    assert user_input.has_pending() is True
    assert await user_input.read_async() == "hello"
    assert user_input.has_pending() is False
