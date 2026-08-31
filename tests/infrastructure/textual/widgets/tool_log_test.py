import pytest
from textual.app import App, ComposeResult
from textual.widgets import TextArea

from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus
from simple_agent.infrastructure.textual.widgets.tool_log import (
    LIVE_ENTRY_WINDOW,
    CollapsedToolEntry,
    ToolCollapsible,
    ToolLog,
)
from tests.infrastructure.textual.test_utils import eventually


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


@pytest.mark.asyncio
async def test_replayed_tool_calls_become_cheap_entries():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)

        tool_log.begin_replay()
        tool_log.add_tool_call("call-1", "🛠️ bash echo hi")
        tool_log.add_tool_result(
            "call-1", SingleToolResult(message="hi", status=ToolResultStatus.SUCCESS)
        )
        tool_log.end_replay()

        assert len(app.query(CollapsedToolEntry)) == 1
        assert not app.query(TextArea)


@pytest.mark.asyncio
async def test_a_replayed_call_without_a_result_stays_a_collapsible():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)

        tool_log.begin_replay()
        tool_log.add_tool_call("call-1", "🛠️ bash sleep 3")
        tool_log.end_replay()

        assert not app.query(CollapsedToolEntry)
        assert tool_log._collapsibles[-1].title == "💲 bash sleep 3"


@pytest.mark.asyncio
async def test_live_tool_calls_still_build_a_collapsible():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)

        tool_log.add_tool_call("call-1", "🛠️ bash echo hi")
        tool_log.add_tool_result(
            "call-1", SingleToolResult(message="hi", status=ToolResultStatus.SUCCESS)
        )

        assert not app.query(CollapsedToolEntry)
        assert tool_log._collapsibles[-1].has_class("tool-status-success")


@pytest.mark.asyncio
async def test_a_replayed_cancelled_call_keeps_its_cancelled_status():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)

        tool_log.begin_replay()
        tool_log.add_tool_call("call-1", "🛠️ bash sleep 10")
        tool_log.add_tool_cancelled("call-1")
        tool_log.end_replay()

        assert tool_log._collapsibles[-1].has_class("tool-status-cancelled")
        assert tool_log._collapsibles[-1].title == "💲 bash sleep 10 (Cancelled)"


@pytest.mark.asyncio
async def test_a_replayed_cancellation_keeps_the_history_in_order():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)

        tool_log.begin_replay()
        tool_log.add_tool_call("call-1", "🛠️ bash echo first")
        tool_log.add_tool_result(
            "call-1", SingleToolResult(message="first", status=ToolResultStatus.SUCCESS)
        )
        tool_log.add_tool_call("call-2", "🛠️ bash sleep 10")
        tool_log.add_tool_cancelled("call-2")
        tool_log.add_tool_call("call-3", "🛠️ bash echo third")
        tool_log.add_tool_result(
            "call-3", SingleToolResult(message="third", status=ToolResultStatus.SUCCESS)
        )
        tool_log.end_replay()

        kinds = [type(child).__name__ for child in tool_log.children]
        assert kinds == ["CollapsedToolEntry", "ToolCollapsible", "CollapsedToolEntry"]


@pytest.mark.asyncio
async def test_replayed_thoughts_keep_their_place_between_tool_calls():
    app = ToolLogApp()
    async with app.run_test():
        tool_log = app.query_one("#tool-log", ToolLog)

        tool_log.begin_replay()
        tool_log.add_tool_call("call-1", "🛠️ bash echo first")
        tool_log.add_tool_result(
            "call-1", SingleToolResult(message="first", status=ToolResultStatus.SUCCESS)
        )
        tool_log.add_thought("thinking it over")
        tool_log.add_tool_call("call-2", "🛠️ bash echo second")
        tool_log.add_tool_result(
            "call-2",
            SingleToolResult(message="second", status=ToolResultStatus.SUCCESS),
        )
        tool_log.end_replay()

        titles = [
            child.title if isinstance(child, ToolCollapsible) else child._entry_title
            for child in tool_log.children
        ]
        assert titles == ["💲 bash echo first", "🧠 thought", "💲 bash echo second"]


@pytest.mark.asyncio
async def test_only_the_most_recent_entries_stay_collapsibles():
    app = ToolLogApp()
    async with app.run_test() as pilot:
        tool_log = app.query_one("#tool-log", ToolLog)

        for i in range(LIVE_ENTRY_WINDOW + 3):
            tool_log.add_tool_call(f"call-{i}", f"🛠️ bash echo {i}")
            tool_log.add_tool_result(
                f"call-{i}",
                SingleToolResult(message=str(i), status=ToolResultStatus.SUCCESS),
            )

        await eventually(
            pilot,
            lambda: len(tool_log.children) == LIVE_ENTRY_WINDOW + 3,
            "the oldest entries to degrade",
        )

        kinds = [type(child).__name__ for child in tool_log.children]
        assert kinds.count("CollapsedToolEntry") == 3
        assert kinds.count("ToolCollapsible") == LIVE_ENTRY_WINDOW
        assert kinds[:3] == ["CollapsedToolEntry"] * 3


@pytest.mark.asyncio
async def test_a_degraded_entry_still_opens_with_its_output():
    app = ToolLogApp()
    async with app.run_test() as pilot:
        tool_log = app.query_one("#tool-log", ToolLog)

        for i in range(LIVE_ENTRY_WINDOW + 1):
            tool_log.add_tool_call(f"call-{i}", f"🛠️ bash echo {i}")
            tool_log.add_tool_result(
                f"call-{i}",
                SingleToolResult(
                    message=f"output {i}", status=ToolResultStatus.SUCCESS
                ),
            )

        await eventually(
            pilot,
            lambda: len(tool_log.children) == LIVE_ENTRY_WINDOW + 1
            and isinstance(tool_log.children[0], CollapsedToolEntry),
            "the oldest entry to degrade",
        )

        oldest = tool_log.children[0]

        upgraded = oldest.upgrade()
        await eventually(
            pilot,
            lambda: upgraded.query(TextArea),
            "the upgraded entry to build its body",
        )

        assert upgraded.title == "💲 bash echo 0"
        assert upgraded.query_one(TextArea).text == "output 0"
        assert upgraded.has_class("tool-status-success")


@pytest.mark.asyncio
async def test_a_running_tool_call_is_never_degraded():
    app = ToolLogApp()
    async with app.run_test() as pilot:
        tool_log = app.query_one("#tool-log", ToolLog)

        tool_log.add_tool_call("still-running", "🛠️ bash sleep 300")
        for i in range(LIVE_ENTRY_WINDOW + 3):
            tool_log.add_tool_call(f"call-{i}", f"🛠️ bash echo {i}")
            tool_log.add_tool_result(
                f"call-{i}",
                SingleToolResult(message=str(i), status=ToolResultStatus.SUCCESS),
            )

        await eventually(
            pilot,
            lambda: len(tool_log.children) == LIVE_ENTRY_WINDOW + 4,
            "the oldest finished entries to degrade",
        )

        assert isinstance(tool_log.children[0], ToolCollapsible)
        assert tool_log.children[0].title == "💲 bash sleep 300"
