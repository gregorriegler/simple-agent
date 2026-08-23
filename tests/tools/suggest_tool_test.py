import pytest

from tests.test_helpers import create_all_tools_for_test, verify_tool

pytestmark = pytest.mark.asyncio


@pytest.fixture
def observer_tools():
    return create_all_tools_for_test(["suggest"])


async def test_suggest_tool(observer_tools):
    await verify_tool(
        observer_tools,
        "🛠️[suggest]\ndata1.txt says nothing about its content\n🛠️[/end]",
    )


async def test_suggest_tool_without_a_suggestion(observer_tools):
    await verify_tool(observer_tools, "🛠️[suggest]\n\n🛠️[/end]")
