import pytest

from simple_agent.application.tool_library import ToolCall
from tests.test_helpers import create_all_tools_for_test, verify_tool
from tests.tool_calls import suggest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def observer_tools():
    return create_all_tools_for_test(["suggest"])


async def test_suggest_tool(observer_tools):
    await verify_tool(
        observer_tools, suggest("data1.txt says nothing about its content")
    )


async def test_suggest_tool_without_a_suggestion(observer_tools):
    await verify_tool(observer_tools, ToolCall("suggest"))
