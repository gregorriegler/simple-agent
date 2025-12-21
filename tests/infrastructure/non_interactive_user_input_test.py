import pytest

from simple_agent.infrastructure.non_interactive_user_input import NonInteractiveUserInput

pytestmark = pytest.mark.asyncio


async def test_non_interactive_user_input_returns_empty_and_no_escape():
    user_input = NonInteractiveUserInput()

    assert await user_input.read_async() == ""
    assert user_input.escape_requested() is False


async def test_non_interactive_user_input_close_is_noop():
    user_input = NonInteractiveUserInput()

    user_input.close()
    user_input.close()
