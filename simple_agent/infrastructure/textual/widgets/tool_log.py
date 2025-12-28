from rich.syntax import Syntax
from textual.containers import VerticalScroll
from textual.widgets import TextArea, Collapsible, Static
from textual.timer import Timer
from textual.css.query import NoMatches
import logging

from simple_agent.application.tool_results import ToolResult

logger = logging.getLogger(__name__)

class ToolLog(VerticalScroll):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # call_id -> (message, text_area, collapsible)
        self._pending_tool_calls: dict[str, tuple[str, TextArea, Collapsible]] = {}
        self._suppressed_tool_calls: set[str] = set()
        self._collapsibles: list[Collapsible] = []
        self.loading_timer: Timer | None = None
        self.loading_frames = ["⠇", "⠏", "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]
        self.loading_frame_index = 0

    def on_unmount(self) -> None:
        if self.loading_timer:
            self.loading_timer.stop()

    def _update_loading_animation(self) -> None:
        frame = self.loading_frames[self.loading_frame_index]
        for _, text_area, _ in self._pending_tool_calls.values():
            text_area.load_text(f"In Progress {frame}")
            text_area.refresh()
        self.loading_frame_index = (self.loading_frame_index + 1) % len(self.loading_frames)

    def _stop_loading_if_idle(self) -> None:
        if not self._pending_tool_calls:
            if self.loading_timer:
                self.loading_timer.stop()
                self.loading_timer = None

    def add_tool_call(self, call_id: str, message: str) -> None:
        if "write-todos" in message:
            self._suppressed_tool_calls.add(call_id)
            return

        for collapsible in self._collapsibles:
            collapsible.collapsed = True

        text_area = TextArea(
            f"In Progress {self.loading_frames[0]}",
            read_only=True,
            language="markdown",
            show_cursor=False,
            classes="tool-call",
        )
        text_area.styles.height = 3
        text_area.styles.min_height = 3

        lines = message.splitlines()
        default_title = lines[0] if lines else "Tool Call"
        collapsible = Collapsible(text_area, title=default_title, collapsed=False)
        self._collapsibles.append(collapsible)

        self._pending_tool_calls[call_id] = (message, text_area, collapsible)
        if self.is_mounted:
            self.mount(collapsible)
            self.scroll_end(animate=False)
            if not self.loading_timer:
                self.loading_timer = self.set_interval(0.1, self._update_loading_animation)

    def compose(self):
        yield from self._collapsibles

    def on_mount(self) -> None:
        if self._pending_tool_calls and not self.loading_timer:
            self.loading_timer = self.set_interval(0.1, self._update_loading_animation)

    def _pop_pending_tool_call(self, call_id: str) -> tuple[tuple[str, TextArea, Collapsible] | None, bool]:
        if call_id in self._suppressed_tool_calls:
            self._suppressed_tool_calls.discard(call_id)
            return None, True
        return self._pending_tool_calls.pop(call_id, None), False

    def add_tool_result(self, call_id: str, result: ToolResult) -> None:
        success = result.success
        pending_entry, suppressed = self._pop_pending_tool_call(call_id)
        if suppressed:
            return

        if pending_entry is None:
            logger.warning(
                "Tool result received with no matching call. call_id=%s",
                call_id,
            )
            self._stop_loading_if_idle()
            return

        title_source, text_area, call_collapsible = pending_entry
        message = result.display_body if result.display_body else result.message
        message = message or ""
        title_text = result.display_title if result.display_title else None
        lines = title_source.splitlines()
        default_title = lines[0] if lines else "Tool Result"
        other_lines = lines[1:]
        if title_text is None:
            title_text = default_title
        if success and other_lines and not result.display_body and not message.strip():
            message = "\n".join(other_lines)

        for existing in self._collapsibles:
            existing.collapsed = True
        call_collapsible.collapsed = False

        classes = "tool-result tool-result-success" if success else "tool-result tool-result-error"
        language = result.display_language or "python"

        if language == "diff":
            diff_renderable = Syntax(
                message,
                "diff",
                theme="ansi_dark",
                line_numbers=False,
                word_wrap=True,
            )
            diff_widget = Static(diff_renderable)
            for cls in classes.split():
                diff_widget.add_class(cls)
            height = min((len(message.splitlines()) or 1) + 2, 30)
            diff_widget.styles.height = height
            diff_widget.styles.min_height = height
            text_area.remove()
            try:
                contents = call_collapsible.query_one(Collapsible.Contents)
                contents.mount(diff_widget)
            except NoMatches:
                logger.warning(
                    "Missing collapsible contents for tool result. call_id=%s",
                    call_id,
                )
                call_collapsible.mount(diff_widget)
        else:
            line_count = len(message.splitlines()) or 1
            height = min(line_count + 2, 30)
            text_area.load_text(message)
            text_area.language = language
            text_area.remove_class("tool-call")
            for cls in ("tool-result", "tool-result-error"):
                text_area.remove_class(cls)
            for cls in classes.split():
                text_area.add_class(cls)
            text_area.styles.height = height
            text_area.styles.min_height = height

        call_collapsible.title = title_text
        self.scroll_end(animate=False)
        self._stop_loading_if_idle()

    def add_tool_cancelled(self, call_id: str) -> None:
        pending_entry, suppressed = self._pop_pending_tool_call(call_id)
        if suppressed:
            self._stop_loading_if_idle()
            return

        if pending_entry is None:
            logger.warning(
                "Tool cancelled with no matching call. call_id=%s",
                call_id,
            )
            self._stop_loading_if_idle()
            return

        title_source, text_area, call_collapsible = pending_entry

        # Update to show cancelled state
        text_area.load_text("Cancelled")
        text_area.remove_class("tool-call")
        text_area.add_class("tool-result")
        text_area.add_class("tool-result-error")
        text_area.styles.height = 3
        text_area.styles.min_height = 3

        lines = title_source.splitlines()
        default_title = lines[0] if lines else "Tool Call"
        call_collapsible.title = f"{default_title} (Cancelled)"

        self.scroll_end(animate=False)
        self._stop_loading_if_idle()

    def clear(self) -> None:
        self.remove_children()
        self._pending_tool_calls.clear()
        self._suppressed_tool_calls.clear()
        self._collapsibles.clear()
        if self.loading_timer:
            self.loading_timer.stop()
            self.loading_timer = None
