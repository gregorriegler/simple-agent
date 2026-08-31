import logging
import re
from collections.abc import Callable

from rich.cells import cell_len
from rich.syntax import Syntax
from rich.text import Text
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widget import Widget
from textual.widgets import Collapsible, Static, TextArea
from textual.widgets._collapsible import CollapsibleTitle

from simple_agent.application.tool_results import ToolResult

logger = logging.getLogger(__name__)


TOOL_EMOJIS = {
    "bash": "💲",
    "cat": "📄",
    "ls": "📁",
    "create-file": "📝",
    "replace-file-content": "📝",
    "subagent": "🤖",
    "complete-task": "🏁",
    "write-todos": "📋",
}
DEFAULT_TOOL_EMOJI = "🛠️"
COLLAPSED_SYMBOL = "▶"
LIVE_ENTRY_WINDOW = 10
THOUGHT_EMOJI = "🧠"
_STATUS_EMOJIS = ("🛠️", "🛠", "✅", "❌", "🚫")
_TITLE_EMOJIS = _STATUS_EMOJIS + tuple(TOOL_EMOJIS.values()) + (THOUGHT_EMOJI,)


def _strip_title_emoji(title: str) -> str:
    for prefix in _TITLE_EMOJIS:
        if title.startswith(prefix):
            return title[len(prefix) :].lstrip()
    return title


def _tool_emoji_for(message: str) -> str:
    first_line = message.splitlines()[0] if message else ""
    parts = _strip_title_emoji(first_line).split(None, 1)
    tool_name = parts[0] if parts else ""
    return TOOL_EMOJIS.get(tool_name, DEFAULT_TOOL_EMOJI)


def _format_tool_title(title: str, emoji: str) -> str:
    return f"{emoji} {_strip_title_emoji(title)}"


def _indented_title(raw_label: str, symbol: str, width: int, console) -> Text:
    match = re.match(r"^(\S+)\s+(.*)$", raw_label)
    if match and any(e in match.group(1) for e in _TITLE_EMOJIS):
        prefix_line1 = f"{symbol} {match.group(1)} "
        body_text = match.group(2)
    else:
        prefix_line1 = f"{symbol} "
        body_text = raw_label

    indent = cell_len(prefix_line1)
    if width <= 0:
        width = 56

    formatted = Text()
    for i, line in enumerate(Text(body_text).wrap(console, max(width - indent, 10))):
        if i == 0:
            formatted.append(prefix_line1)
        else:
            formatted.append("\n" + (" " * indent))
        formatted.append(line)
    return formatted


class ToolCollapsible(Collapsible):
    def _update_indented_title(self) -> None:
        title_widget = self._title
        symbol = (
            title_widget.collapsed_symbol
            if title_widget.collapsed
            else title_widget.expanded_symbol
        )
        raw_label = (
            title_widget.label.plain
            if hasattr(title_widget.label, "plain")
            else str(title_widget.label)
        )

        title_widget.update(
            _indented_title(
                raw_label,
                symbol,
                title_widget.size.width - 2,
                self.app.console if self.app else None,
            )
        )

    def on_mount(self) -> None:
        self._update_indented_title()
        self.call_after_refresh(self._update_indented_title)

    def on_resize(self) -> None:
        if self.is_mounted:
            self._update_indented_title()

    def _watch_collapsed(self, collapsed: bool) -> None:
        super()._watch_collapsed(collapsed)
        if self.is_mounted:
            self._update_indented_title()

    def _watch_title(self, title: str) -> None:
        super()._watch_title(title)
        if self.is_mounted:
            self._update_indented_title()


def _result_body(result: ToolResult) -> Static | TextArea:
    message = result.display_body or result.message or "No output"
    language = result.display_language or "python"
    height = min((len(message.splitlines()) or 1) + 2, 30)

    if language == "diff":
        body = Static(
            Syntax(
                message, "diff", theme="ansi_dark", line_numbers=False, word_wrap=True
            )
        )
    else:
        body = TextArea(message, read_only=True, language=language, show_cursor=False)
    body.styles.height = height
    body.add_class("tool-result")
    body.add_class("tool-result-success" if result.success else "tool-result-error")
    return body


def _status_class_for(result: ToolResult) -> str:
    if result.cancelled:
        return "tool-status-cancelled"
    return "tool-status-success" if result.success else "tool-status-error"


def _focus_title_of(collapsible: ToolCollapsible) -> None:
    try:
        collapsible.query_one(CollapsibleTitle).focus()
    except NoMatches:
        pass


class CollapsedToolEntry(Static, can_focus=True):
    def __init__(
        self,
        title: str,
        build_body: Callable[[], Widget],
        status_class: str,
        **kwargs,
    ):
        super().__init__(Text(f"{COLLAPSED_SYMBOL} {title}"), **kwargs)
        self._entry_title = title
        self._build_body = build_body
        self._status_class = status_class
        self.add_class(status_class)

    @classmethod
    def of_result(cls, title: str, result: ToolResult) -> "CollapsedToolEntry":
        return cls(title, lambda: _result_body(result), _status_class_for(result))

    @classmethod
    def of_thought(cls, title: str, thought: str) -> "CollapsedToolEntry":
        return cls(title, lambda: Static(Text(thought), classes="thought"), "thought")

    def on_mount(self) -> None:
        self._refresh_title()
        self.call_after_refresh(self._refresh_title)

    def on_resize(self) -> None:
        if self.is_mounted:
            self._refresh_title()

    BINDINGS = [Binding("enter", "upgrade", "Open", show=False)]

    def on_click(self) -> None:
        self.upgrade()

    def action_upgrade(self) -> None:
        self.upgrade()

    def upgrade(self) -> ToolCollapsible:
        collapsible = ToolCollapsible(
            self._build_body(),
            title=self._entry_title,
            collapsed=False,
            classes=self._status_class,
        )
        self.parent.mount(collapsible, after=self)
        self.remove()
        collapsible.call_after_refresh(_focus_title_of, collapsible)
        return collapsible

    def _refresh_title(self) -> None:
        self.update(
            _indented_title(
                self._entry_title,
                COLLAPSED_SYMBOL,
                self.size.width - 2,
                self.app.console if self.app else None,
            )
        )


class ToolLog(VerticalScroll):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pending_tool_calls = {}
        self._suppressed_tool_calls = set()
        self._collapsibles = []
        self._deferred_loading: set[str] = set()
        self._replaying = False
        self._replayed_calls: dict[str, str] = {}
        self._replayed_widgets: list[Widget] = []

    def begin_replay(self) -> None:
        self._replaying = True

    def end_replay(self) -> None:
        self._replaying = False
        self._mount_replayed_widgets()
        unfinished = self._replayed_calls
        self._replayed_calls = {}
        for call_id, message in unfinished.items():
            self.add_tool_call(call_id, message)

    def _add_replayed_entry(self, call_id: str, result: ToolResult) -> None:
        message = self._replayed_calls.pop(call_id, None) or (
            result.display_title or "Recovered Tool Call"
        )
        title = message.splitlines()[0] if message else "Tool Call"
        title = _format_tool_title(
            result.display_title or title, _tool_emoji_for(message)
        )
        self._replayed_widgets.append(CollapsedToolEntry.of_result(title, result))

    def _materialise_replayed_call(self, call_id: str) -> None:
        message = self._replayed_calls.pop(call_id, None)
        if message is None:
            return

        self._mount_replayed_widgets()
        self._replaying = False
        try:
            self.add_tool_call(call_id, message)
        finally:
            self._replaying = True

    def _degrade_old_entries(self) -> None:
        excess = len(self._collapsibles) - LIVE_ENTRY_WINDOW
        for collapsible in self._collapsibles[: max(excess, 0)]:
            imitate = getattr(collapsible, "_imitate", None)
            if imitate is None or collapsible.parent is None:
                continue
            collapsible.parent.mount(imitate(), after=collapsible)
            collapsible.remove()
            self._collapsibles.remove(collapsible)

    def _mount_replayed_widgets(self) -> None:
        orphans = [e for e in self._replayed_widgets if e.parent is None]
        if orphans and self.is_mounted:
            self.mount(*orphans)
            self.scroll_end(animate=False)

    def add_tool_call(self, call_id: str, message: str) -> None:
        if "write-todos" in message:
            self._suppressed_tool_calls.add(call_id)
            return

        if self._replaying:
            self._replayed_calls[call_id] = message
            return

        for collapsible in self._collapsibles:
            collapsible.collapsed = True

        text_area = TextArea(
            "",
            read_only=True,
            language="markdown",
            show_cursor=False,
            classes="tool-call",
        )
        text_area.styles.height = 3

        title = message.splitlines()[0] if message else "Tool Call"
        title = _format_tool_title(title, _tool_emoji_for(message))
        collapsible = ToolCollapsible(
            text_area,
            title=title,
            collapsed=False,
            classes="tool-status-running",
        )
        self._collapsibles.append(collapsible)
        self._pending_tool_calls[call_id] = (message, text_area, collapsible)

        if self.is_mounted:
            self.mount(collapsible)
            self.scroll_end(animate=False)
            self._degrade_old_entries()

        # Defer showing the loading spinner to the next frame.
        # If add_tool_result arrives before then, no spinner is ever shown.
        self._deferred_loading.add(call_id)
        self.call_later(self._show_loading, call_id)

    def add_thought(self, thought: str) -> None:
        for collapsible in self._collapsibles:
            collapsible.collapsed = True

        collapsible = ToolCollapsible(
            Static(Text(thought), classes="thought"),
            title=f"{THOUGHT_EMOJI} thought",
            collapsed=True,
            classes="thought",
        )
        collapsible._imitate = lambda: CollapsedToolEntry.of_thought(
            f"{THOUGHT_EMOJI} thought", thought
        )
        self._collapsibles.append(collapsible)

        if self._replaying:
            self._replayed_widgets.append(collapsible)
            return

        if self.is_mounted:
            self.mount(collapsible)
            self.scroll_end(animate=False)

    def _show_loading(self, call_id: str) -> None:
        if call_id not in self._deferred_loading:
            return
        self._deferred_loading.discard(call_id)
        if call_id in self._pending_tool_calls:
            _, text_area, _ = self._pending_tool_calls[call_id]
            text_area.loading = True

    def _cancel_deferred_loading(self, call_id: str) -> None:
        self._deferred_loading.discard(call_id)

    def on_mount(self) -> None:
        self._mount_replayed_widgets()
        for collapsible in self._collapsibles:
            if collapsible.parent is None:
                self.mount(collapsible)
        self.scroll_end(animate=False)

    def add_tool_result(self, call_id: str, result: ToolResult) -> None:
        if call_id in self._suppressed_tool_calls:
            return

        if self._replaying:
            self._add_replayed_entry(call_id, result)
            return

        self._cancel_deferred_loading(call_id)

        if call_id not in self._pending_tool_calls:
            self.add_tool_call(call_id, result.display_title or "Recovered Tool Call")
            self._cancel_deferred_loading(call_id)

        orig_message, text_area, call_collapsible = self._pending_tool_calls.pop(
            call_id
        )
        message = result.display_body or result.message or "No output"
        language = result.display_language or "python"
        classes = (
            "tool-result tool-result-success"
            if result.success
            else "tool-result tool-result-error"
        )

        text_area.loading = False

        if language == "diff":
            diff_widget = Static(
                Syntax(
                    message,
                    "diff",
                    theme="ansi_dark",
                    line_numbers=False,
                    word_wrap=True,
                )
            )
            for cls in classes.split():
                diff_widget.add_class(cls)
            height = min((len(message.splitlines()) or 1) + 2, 30)
            diff_widget.styles.height = height
            text_area.remove()
            try:
                contents = call_collapsible.query_one(Collapsible.Contents)
                contents.mount(diff_widget)
            except NoMatches:
                call_collapsible.mount(diff_widget)
        else:
            text_area.load_text(message)
            text_area.language = language
            text_area.remove_class("tool-call")
            for cls in classes.split():
                text_area.add_class(cls)
            text_area.styles.height = min((len(message.splitlines()) or 1) + 2, 30)

        status_class = (
            "tool-status-cancelled"
            if result.cancelled
            else ("tool-status-success" if result.success else "tool-status-error")
        )
        call_collapsible.remove_class(
            "tool-status-running",
            "tool-status-success",
            "tool-status-error",
            "tool-status-cancelled",
        )
        call_collapsible.add_class(status_class)
        base_title = result.display_title or call_collapsible.title
        call_collapsible.title = _format_tool_title(
            base_title, _tool_emoji_for(orig_message)
        )
        call_collapsible._imitate = lambda: CollapsedToolEntry.of_result(
            call_collapsible.title, result
        )

        if self.is_mounted:
            self.scroll_end(animate=False)

    def add_tool_cancelled(self, call_id: str) -> None:
        if call_id in self._suppressed_tool_calls:
            self._suppressed_tool_calls.discard(call_id)
            return

        if self._replaying:
            self._materialise_replayed_call(call_id)

        self._cancel_deferred_loading(call_id)

        pending_entry = self._pending_tool_calls.pop(call_id, None)
        if pending_entry is None:
            logger.warning("Tool cancelled with no matching call. call_id=%s", call_id)
            return

        title_source, text_area, call_collapsible = pending_entry
        text_area.loading = False
        text_area.load_text("Cancelled")
        text_area.remove_class("tool-call")
        text_area.add_class("tool-result")
        text_area.add_class("tool-result-error")
        text_area.styles.height = 3

        call_collapsible.remove_class(
            "tool-status-running",
            "tool-status-success",
            "tool-status-error",
            "tool-status-cancelled",
        )
        call_collapsible.add_class("tool-status-cancelled")
        title = title_source.splitlines()[0] if title_source else "Tool Call"
        call_collapsible.title = (
            f"{_format_tool_title(title, _tool_emoji_for(title_source))} (Cancelled)"
        )

        if self.is_mounted:
            self.scroll_end(animate=False)

    def clear(self) -> None:
        self._deferred_loading.clear()
        self.remove_children()
        self._pending_tool_calls.clear()
        self._suppressed_tool_calls.clear()
        self._collapsibles.clear()
        self._replayed_calls.clear()
        self._replayed_widgets.clear()
