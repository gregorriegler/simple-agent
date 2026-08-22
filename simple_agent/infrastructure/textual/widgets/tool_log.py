import logging
import re

from rich.cells import cell_len
from rich.syntax import Syntax
from rich.text import Text
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Collapsible, Static, TextArea

from simple_agent.application.tool_results import ToolResult

logger = logging.getLogger(__name__)


def _format_tool_title(title: str, status_emoji: str) -> str:
    for prefix in ("🛠️", "🛠", "✅", "❌", "🚫"):
        if title.startswith(prefix):
            title = title[len(prefix) :].lstrip()
            break
    return f"{status_emoji} {title}"


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

        match = re.match(r"^(\S+)\s+(.*)$", raw_label)
        if match and any(e in match.group(1) for e in ("🛠", "✅", "❌", "🚫")):
            prefix_line1 = f"{symbol} {match.group(1)} "
            body_text = match.group(2)
        else:
            prefix_line1 = f"{symbol} "
            body_text = raw_label

        indent = cell_len(prefix_line1)
        width = title_widget.size.width - 2
        if width <= 0:
            width = 56
        wrap_width = max(width - indent, 10)

        console = self.app.console if self.app else None
        wrapped_lines = Text(body_text).wrap(console, wrap_width)

        formatted = Text()
        for i, line in enumerate(wrapped_lines):
            if i == 0:
                formatted.append(prefix_line1)
                formatted.append(line)
            else:
                formatted.append("\n" + (" " * indent))
                formatted.append(line)

        title_widget.update(formatted)

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


class ToolLog(VerticalScroll):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pending_tool_calls = {}
        self._suppressed_tool_calls = set()
        self._collapsibles = []
        self._deferred_loading: set[str] = set()

    def add_tool_call(self, call_id: str, message: str) -> None:
        if "write-todos" in message:
            self._suppressed_tool_calls.add(call_id)
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
        collapsible = ToolCollapsible(text_area, title=title, collapsed=False)
        self._collapsibles.append(collapsible)
        self._pending_tool_calls[call_id] = (message, text_area, collapsible)

        if self.is_mounted:
            self.mount(collapsible)
            self.scroll_end(animate=False)

        # Defer showing the loading spinner to the next frame.
        # If add_tool_result arrives before then, no spinner is ever shown.
        self._deferred_loading.add(call_id)
        self.call_later(self._show_loading, call_id)

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
        for collapsible in self._collapsibles:
            if collapsible.parent is None:
                self.mount(collapsible)
        self.scroll_end(animate=False)

    def add_tool_result(self, call_id: str, result: ToolResult) -> None:
        if call_id in self._suppressed_tool_calls:
            return

        self._cancel_deferred_loading(call_id)

        if call_id not in self._pending_tool_calls:
            self.add_tool_call(call_id, result.display_title or "Recovered Tool Call")
            self._cancel_deferred_loading(call_id)

        _, text_area, call_collapsible = self._pending_tool_calls.pop(call_id)
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

        status_emoji = "🚫" if result.cancelled else ("✅" if result.success else "❌")
        base_title = result.display_title or call_collapsible.title
        call_collapsible.title = _format_tool_title(base_title, status_emoji)

        if self.is_mounted:
            self.scroll_end(animate=False)

    def add_tool_cancelled(self, call_id: str) -> None:
        if call_id in self._suppressed_tool_calls:
            self._suppressed_tool_calls.discard(call_id)
            return

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

        title = title_source.splitlines()[0] if title_source else "Tool Call"
        call_collapsible.title = f"{_format_tool_title(title, '🚫')} (Cancelled)"

        if self.is_mounted:
            self.scroll_end(animate=False)

    def clear(self) -> None:
        self._deferred_loading.clear()
        self.remove_children()
        self._pending_tool_calls.clear()
        self._suppressed_tool_calls.clear()
        self._collapsibles.clear()
