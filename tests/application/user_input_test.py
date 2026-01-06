import pytest

pytestmark = pytest.mark.asyncio

from simple_agent.application.user_input import DummyUserInput


async def test_dummy_user_input_returns_empty_prompt_and_no_escape_request():
    user_input = DummyUserInput()

    assert await user_input.read_async() == ""
    assert user_input.escape_requested() is False


async def test_dummy_user_input_close_is_noop():
    user_input = DummyUserInput()

    user_input.close()
    # Should be callable multiple times without raising
    user_input.close()
