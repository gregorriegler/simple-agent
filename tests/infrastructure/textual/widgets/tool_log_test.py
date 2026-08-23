import pytest
from textual.app import App, ComposeResult

from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog


class ToolLogApp(App):
    CSS = """
    CollapsibleTitle {
        width: 100%;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield ToolLog(id="tool-log")


@pytest.mark.asyncio
async def test_a_running_tool_call_has_the_running_status_class():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)

        tool_log.add_tool_call("call-1", "🛠️ bash sleep 3")

        assert tool_log._collapsibles[-1].has_class("tool-status-running")


@pytest.mark.asyncio
async def test_tool_log_success_retains_tool_emoji_with_success_border():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", "🛠️ bash sleep 3")

        assert tool_log._collapsibles[-1].title == "💲 bash sleep 3"

        result = SingleToolResult(message="ok", status=ToolResultStatus.SUCCESS)
        tool_log.add_tool_result("call-1", result)

        assert tool_log._collapsibles[-1].title == "💲 bash sleep 3"
        assert tool_log._collapsibles[-1].has_class("tool-status-success")


@pytest.mark.asyncio
async def test_tool_log_failure_retains_tool_emoji_with_error_border():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", "🛠️ cat missing.txt")

        result = SingleToolResult(
            message="No such file", status=ToolResultStatus.FAILURE
        )
        tool_log.add_tool_result("call-1", result)

        assert tool_log._collapsibles[-1].title == "📄 cat missing.txt"
        assert tool_log._collapsibles[-1].has_class("tool-status-error")


@pytest.mark.asyncio
async def test_tool_log_cancelled_retains_tool_emoji_with_cancelled_border():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", "🛠️ bash sleep 10")

        tool_log.add_tool_cancelled("call-1")

        assert tool_log._collapsibles[-1].title == "💲 bash sleep 10 (Cancelled)"
        assert tool_log._collapsibles[-1].has_class("tool-status-cancelled")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, emoji",
    [
        ("bash", "💲"),
        ("cat", "📄"),
        ("ls", "📁"),
        ("create-file", "📝"),
        ("replace-file-content", "📝"),
        ("subagent", "🤖"),
        ("complete-task", "🏁"),
    ],
)
async def test_tool_log_maps_each_tool_to_its_emoji(name, emoji):
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", f"🛠️ {name} some args")

        assert tool_log._collapsibles[-1].title == f"{emoji} {name} some args"


@pytest.mark.asyncio
async def test_tool_log_unknown_tool_keeps_wrench_emoji():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", "🛠️ search_files query=test")

        result = SingleToolResult(
            message="Found 1 file",
            display_title="Search Results",
            status=ToolResultStatus.SUCCESS,
        )
        tool_log.add_tool_result("call-1", result)

        assert tool_log._collapsibles[-1].title == "🛠️ Search Results"
        assert tool_log._collapsibles[-1].has_class("tool-status-success")


@pytest.mark.asyncio
async def test_tool_log_wrapped_title_has_hanging_indent():
    app = ToolLogApp()
    long_command = "🛠️ bash sleep 3 && echo 'this is a very long command with lots of arguments and options that will wrap to multiple lines'"
    async with app.run_test(size=(60, 15)) as pilot:
        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", long_command)
        await pilot.pause()

        collapsible = tool_log._collapsibles[-1]
        title_content = collapsible._title.render()
        lines = title_content.plain.splitlines()
        assert len(lines) > 1
        # Line 0 starts with '▼ 💲 ' (tool-specific symbol for bash)
        assert lines[0].startswith("▼ 💲 ")
        # Line 1 hanging indent aligns with body text after '▼ 💲 ' (5 cells)
        assert lines[1].startswith("     with lots of arguments")


@pytest.mark.asyncio
async def test_tool_log_title_wrapped_on_mount_without_resize():
    app = ToolLogApp()
    long_command = "🛠️ bash sleep 3 && echo 'this is a very long command with lots of arguments and options that will wrap to multiple lines'"
    async with app.run_test(size=(60, 15)) as pilot:
        # Let the app fully lay out first, so mounting the tool call afterwards
        # does NOT trigger an initial resize event (as happens in the real app).
        await pilot.pause()

        tool_log = app.query_one("#tool-log", ToolLog)
        tool_log.add_tool_call("call-1", long_command)
        await pilot.pause()

        collapsible = tool_log._collapsibles[-1]
        lines = collapsible._title.render().plain.splitlines()
        assert len(lines) > 1
        assert lines[0].startswith("▼ 💲 ")
        assert lines[1].startswith("     with lots of arguments")
