import pytest
from textual.app import App, ComposeResult

from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog


class ToolLogApp(App):
    def compose(self) -> ComposeResult:
        yield ToolLog(id="tool-log")


@pytest.mark.asyncio
async def test_tool_log_success_replaces_tool_emoji_with_check():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", "🛠️ bash sleep 3")

        assert tool_log._collapsibles[-1].title == "🛠️ bash sleep 3"

        result = SingleToolResult(message="ok", status=ToolResultStatus.SUCCESS)
        tool_log.add_tool_result("call-1", result)

        assert tool_log._collapsibles[-1].title == "✅ bash sleep 3"


@pytest.mark.asyncio
async def test_tool_log_failure_replaces_tool_emoji_with_cross():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", "🛠️ cat missing.txt")

        result = SingleToolResult(
            message="No such file", status=ToolResultStatus.FAILURE
        )
        tool_log.add_tool_result("call-1", result)

        assert tool_log._collapsibles[-1].title == "❌ cat missing.txt"


@pytest.mark.asyncio
async def test_tool_log_cancelled_replaces_tool_emoji_with_prohibited_and_cancelled_suffix():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", "🛠️ bash sleep 10")

        tool_log.add_tool_cancelled("call-1")

        assert tool_log._collapsibles[-1].title == "🚫 bash sleep 10 (Cancelled)"


@pytest.mark.asyncio
async def test_tool_log_with_custom_display_title():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", "🛠️ search_files(query='test')")

        result = SingleToolResult(
            message="Found 1 file",
            display_title="Search Results",
            status=ToolResultStatus.SUCCESS,
        )
        tool_log.add_tool_result("call-1", result)

        assert tool_log._collapsibles[-1].title == "✅ Search Results"
