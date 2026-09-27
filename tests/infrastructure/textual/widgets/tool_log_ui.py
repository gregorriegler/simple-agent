from rich.cells import cell_len
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Collapsible, Markdown, TextArea

from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus
from simple_agent.infrastructure.textual.widgets.tool_log import (
    CollapsedToolEntry,
    ToolCollapsible,
    ToolLog,
)
from tests.infrastructure.textual.test_utils import eventually


def _fills_its_width(title: Widget) -> bool:
    width = title.size.width - 2
    lines = title.render().plain.splitlines()
    return (
        width > 0
        and len(lines) > 1
        and all(
            cell_len(line) + 1 + cell_len(next_line.split()[0]) > width
            for line, next_line in zip(lines, lines[1:], strict=False)
        )
    )


class ToolLogApp(App):
    CSS = """
    CollapsibleTitle {
        width: 100%;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        yield ToolLog()


class ToolLogUi:
    def __init__(self, tool_log: ToolLog, pilot):
        self._tool_log = tool_log
        self._pilot = pilot

    def call(self, command: str) -> None:
        self._tool_log.add_tool_call(command, f"🛠️ {command}")

    def run(self, command: str, output: str = "ok") -> None:
        self.call(command)
        self.succeed(command, output)

    def succeed(self, command: str, output: str = "ok") -> None:
        self.finish(command, SingleToolResult(output, ToolResultStatus.SUCCESS))

    def fail(self, command: str, output: str) -> None:
        self.finish(command, SingleToolResult(output, ToolResultStatus.FAILURE))

    def finish(self, command: str, result: SingleToolResult) -> None:
        self._tool_log.add_tool_result(command, result)

    def cancel(self, command: str) -> None:
        self._tool_log.add_tool_cancelled(command)

    def think(self, thought: str) -> None:
        self._tool_log.add_thought(thought)

    def begin_replay(self) -> None:
        self._tool_log.begin_replay()

    def end_replay(self) -> None:
        self._tool_log.end_replay()

    async def click(self, command: str) -> None:
        entry = self._entry(command)
        target = entry._title if isinstance(entry, ToolCollapsible) else entry
        await eventually(
            self._pilot, lambda: target.region.height, f"{command} to be laid out"
        )
        self._tool_log.scroll_to_widget(target, animate=False)
        await eventually(
            self._pilot,
            lambda: self._tool_log.region.contains_region(target.region),
            f"{command} to scroll into view",
        )
        await self._pilot.click(target)

    async def outline(self) -> str:
        await eventually(
            self._pilot,
            lambda: all(
                entry.query(Collapsible.Contents)
                for entry in self._entries()
                if isinstance(entry, ToolCollapsible)
            ),
            "every entry to be composed",
        )
        return "\n".join(_outline(entry) for entry in self._entries())

    async def lay_out(self) -> None:
        await self._pilot.pause()

    async def wrapped_title(self, command: str) -> str:
        title = self._entry(command)._title
        await eventually(
            self._pilot,
            lambda: _fills_its_width(title),
            f"{command} to wrap at its width",
        )
        return "\n".join(line.rstrip() for line in title.render().plain.splitlines())

    async def body(self, command: str) -> Widget:
        await eventually(
            self._pilot,
            lambda: not self._body(command).has_class("tool-call"),
            f"{command} to show its result",
        )
        return self._body(command)

    async def markdown_layout(self, command: str) -> tuple[list[int], int]:
        markdown = await self.body(command)

        def blocks():
            return markdown.query("MarkdownBlock")

        await eventually(
            self._pilot,
            lambda: blocks() and all(block.region.height for block in blocks()),
            f"the markdown of {command} to be laid out",
        )
        top = markdown.content_region.y
        rows = [block.region.y - top for block in blocks()]
        return rows, markdown.content_region.height

    def _body(self, command: str) -> Widget:
        contents = self._entry(command).query_one(Collapsible.Contents)
        return next(child for child in contents.children if child.display)

    def _entries(self) -> list[Widget]:
        return [child for child in self._tool_log.children if child.display]

    def _entry(self, command: str) -> Widget:
        return next(e for e in self._entries() if _command(e) == command)


def _outline(entry: Widget) -> str:
    if isinstance(entry, CollapsedToolEntry):
        return f"▶ {_title(entry)}{_status(entry)} · cheap"
    symbol = "▶" if entry.collapsed else "▼"
    lines = [f"{symbol} {_title(entry)}{_status(entry)}"]
    if not entry.collapsed:
        lines += [f"    {line}" for line in _body_text(entry).splitlines()]
    return "\n".join(lines)


def _title(entry: Widget) -> str:
    if isinstance(entry, CollapsedToolEntry):
        return entry._entry_title
    return entry.title


def _command(entry: Widget) -> str:
    _, command = _title(entry).split(" ", 1)
    return command.removesuffix(" (Cancelled)")


def _status(entry: Widget) -> str:
    statuses = [c for c in entry.classes if c.startswith("tool-status-")]
    return "".join(f" · {s.removeprefix('tool-status-')}" for s in statuses)


def _body_text(collapsible: ToolCollapsible) -> str:
    for body in collapsible.query_one(Collapsible.Contents).displayed_children:
        if isinstance(body, TextArea):
            return body.text
        if isinstance(body, Markdown):
            return body.source
    return ""
