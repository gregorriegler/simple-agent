import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.user_input import DummyUserInput

pytestmark = pytest.mark.asyncio


async def test_dummy_user_input_returns_empty_prompt_and_no_escape_request():
    user_input = DummyUserInput()

    assert await user_input.read_async(AgentId("Agent")) == ""
    assert user_input.escape_requested() is False


async def test_dummy_user_input_close_is_noop():
    user_input = DummyUserInput()

    user_input.close()
    # Should be callable multiple times without raising
    user_input.close()
