import asyncio
from dataclasses import dataclass
from typing import Any, Optional
from textual.widgets import Static
from textual.geometry import Offset, Size
from rich.text import Text
from textual.message import Message
from textual.app import ComposeResult

from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    CompletionSearch,
    CompletionResult,
    Suggestion,
    CursorAndLine
)


@dataclass
class PopupAnchor:
    """Encapsulates the visual state needed to position the popup."""
    cursor_offset: Offset
    screen_size: Size

    def get_placement(self, popup_size: Size) -> Offset:
        """
        Calculate the best position for the popup given its size.
        """
        popup_height = popup_size.height
        popup_width = popup_size.width

        if popup_height < 1:
            popup_height = 1
        if popup_width < 1:
            popup_width = 1

        below_y = self.cursor_offset.y + 1
        above_y = self.cursor_offset.y - popup_height

        # Default to below if it fits, otherwise try above, else clamp
        if below_y + popup_height <= self.screen_size.height:
            y = below_y
        elif above_y >= 0:
            y = above_y
        else:
            y = max(0, min(below_y, self.screen_size.height - popup_height))

        # Horizontal positioning
        anchor_x = self.cursor_offset.x - 2
        max_x = max(0, self.screen_size.width - popup_width)
        x = min(max(anchor_x, 0), max_x)

        return Offset(x, y)

    @property
    def max_width(self) -> int:
        return self.screen_size.width


class AutocompletePopup(Static):
    DEFAULT_CSS = """
    AutocompletePopup {
        background: $surface;
        color: $text;
        padding: 0 1;
        overlay: screen;
        layer: overlay;
        display: none;
        border: solid $accent;
    }
    """

    class Selected(Message):
        def __init__(self, item: CompletionResult):
            self.item = item
            super().__init__()

    def __init__(self, autocompleter: Autocompleter, **kwargs):
        """
        Initialize the AutocompletePopup.

        Args:
            autocompleter: Autocompleter instance to use.
            **kwargs: Arguments to pass to the superclass (Static).
        """
        super().__init__(**kwargs)
        self.autocompleter = autocompleter

        self._current_suggestions: list[Suggestion] = []
        self._selected_index: int = 0
        self._active_search: CompletionSearch | None = None
        self._anchor_x: int | None = None

    async def handle_key(self, key: str) -> bool | CompletionResult:
        if not self.display:
            return False

        if key in ("down", "up"):
            self._navigate(key)
            return True

        if key in ("tab", "enter"):
            selection = self._get_selection()
            return selection if selection else True

        if key == "escape":
            self.hide()
            return True

        return False

    def check(self, cursor_and_line: CursorAndLine, anchor: PopupAnchor) -> None:
        search = self.autocompleter.check(cursor_and_line)
        if search.is_triggered():
            self._active_search = search
            asyncio.create_task(self._fetch_suggestions(search, anchor))
        else:
            self.hide()

    def hide(self) -> None:
        self.display = False
        self._current_suggestions = []
        self._selected_index = 0
        self._anchor_x = None
        self._active_search = None

    async def _fetch_suggestions(
        self,
        search: CompletionSearch,
        anchor: PopupAnchor
    ) -> None:
        if self._active_search is not search:
            return

        suggestions = await search.get_suggestions()

        if self._active_search is search:
            if suggestions:
                self._show_suggestions(suggestions, anchor)
            else:
                self.hide()

    def _show_suggestions(
        self,
        suggestions: list[Suggestion],
        anchor: PopupAnchor,
    ) -> None:
        was_visible = self.display
        self._current_suggestions = suggestions
        self._selected_index = 0
        self.display = True

        if not was_visible:
            self._anchor_x = anchor.cursor_offset.x

        self._update_display(anchor)

    def _navigate(self, direction: str) -> None:
        if not self._current_suggestions:
            return

        if direction == "down":
            self._selected_index = (self._selected_index + 1) % len(self._current_suggestions)
        elif direction == "up":
            self._selected_index = (self._selected_index - 1) % len(self._current_suggestions)

        self._render_content()

    def _get_selection(self) -> CompletionResult | None:
        if not self._current_suggestions or self._selected_index >= len(self._current_suggestions):
            return None

        selected = self._current_suggestions[self._selected_index]
        self.hide()
        return selected.to_completion_result()

    def _update_display(self, anchor: PopupAnchor) -> None:
        lines = [item.display_text for item in self._current_suggestions]

        if not lines:
            self.hide()
            return

        max_line_length = max(len(line) for line in lines)
        popup_width = min(max_line_length + 2, anchor.max_width)
        available_width = max(1, popup_width - 2)
        trimmed_lines = [line[:available_width] for line in lines]
        popup_height = len(trimmed_lines)

        self.styles.width = popup_width
        self.styles.height = popup_height

        effective_cursor_offset = anchor.cursor_offset
        if self._anchor_x is not None:
             effective_cursor_offset = Offset(self._anchor_x, anchor.cursor_offset.y)

        placement_anchor = PopupAnchor(
            cursor_offset=effective_cursor_offset,
            screen_size=anchor.screen_size
        )

        offset = placement_anchor.get_placement(Size(popup_width, popup_height))
        self.styles.offset = offset
        self.absolute_offset = offset

        self._render_content(trimmed_lines)

    def _render_content(self, lines: list[str] | None = None) -> None:
        if lines is None:
            if not self._current_suggestions:
                return

            # Re-derive width/lines
            width = self.styles.width
            popup_width = int(width.value) if width and hasattr(width, 'value') else 20
            available_width = max(1, popup_width - 2)
            raw_lines = [item.display_text for item in self._current_suggestions]
            lines = [line[:available_width] for line in raw_lines]

        rendered = Text()
        for index, line in enumerate(lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == self._selected_index else ""
            rendered.append(line, style=style)

        self.update(rendered)

    # Delegate methods for backward compatibility if needed, or remove them
    def action_cursor_down(self) -> None:
        self._navigate("down")

    def action_cursor_up(self) -> None:
        self._navigate("up")

    def action_select(self) -> None:
        res = self._get_selection()
        if res:
            self.post_message(self.Selected(res))
