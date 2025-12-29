import asyncio
from typing import Any, Optional
from textual.widgets import Static
from textual.geometry import Offset, Size
from rich.text import Text

from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    CompletionSearch,
    CompletionResult,
    Suggestion,
    InputContext
)


class AutocompletePopup(Static):
    DEFAULT_CSS = """
    AutocompletePopup {
        background: $surface;
        color: $text;
        padding: 0 1;
        overlay: screen;
        layer: overlay;
        display: none;
    }
    """

    def __init__(self, autocompleters: list[Autocompleter] | None = None, **kwargs):
        """
        Initialize the AutocompletePopup.

        Args:
            autocompleters: Optional list of autocompleter instances to use.
            **kwargs: Arguments to pass to the superclass (Static).
        """
        super().__init__(**kwargs)
        self.autocompleters = autocompleters or []

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
            return self._get_selection()

        if key == "escape":
            self.hide()
            return True

        return False

    def check(self, context: InputContext, cursor_screen_offset: Offset, screen_size: Size) -> None:
        for autocompleter in self.autocompleters:
            search = autocompleter.check(context)
            if search:
                self._active_search = search
                asyncio.create_task(self._fetch_suggestions(search, cursor_screen_offset, screen_size))
                return

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
        cursor_screen_offset: Offset,
        screen_size: Size
    ) -> None:
        # Check if the search is still active (identity check)
        if self._active_search is not search:
            return

        suggestions = await search.get_suggestions()

        # Check again after await
        if self._active_search is search:
            if suggestions:
                self._show_suggestions(suggestions, cursor_screen_offset, screen_size)
            else:
                self.hide()

    def _show_suggestions(
        self,
        suggestions: list[Suggestion],
        cursor_offset: Offset,
        screen_size: Size,
    ) -> None:
        was_visible = self.display
        self._current_suggestions = suggestions
        self._selected_index = 0
        self.display = True

        if not was_visible:
            self._anchor_x = cursor_offset.x

        self._update_display(cursor_offset, screen_size)

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

        # No need to check _active_search strictly here if we trust the display state,
        # but it's good practice.
        if not self._active_search:
            return None

        selected = self._current_suggestions[self._selected_index]
        self.hide()

        # The Suggestion now encapsulates the logic to create a full CompletionResult,
        # including the start_offset which was injected when the Suggestion was created.
        return selected.to_completion_result()

    def _update_display(self, cursor_offset: Offset, screen_size: Size) -> None:
        lines = [item.display_text for item in self._current_suggestions]

        if not lines:
            self.hide()
            return

        max_line_length = max(len(line) for line in lines)
        popup_width = min(max_line_length + 2, screen_size.width)
        available_width = max(1, popup_width - 2)
        trimmed_lines = [line[:available_width] for line in lines]
        popup_height = len(trimmed_lines)

        self.styles.width = popup_width
        self.styles.height = popup_height

        if self._anchor_x is not None:
            target_x = self._anchor_x
        else:
            target_x = cursor_offset.x

        target_offset = Offset(target_x, cursor_offset.y)

        self.absolute_offset = self._calculate_position(
            cursor_offset=target_offset,
            screen_size=screen_size,
            popup_height=popup_height,
            popup_width=popup_width,
        )

        self._render_content(trimmed_lines)

    @staticmethod
    def _calculate_position(
        cursor_offset: Offset,
        screen_size: Size,
        popup_height: int,
        popup_width: int,
    ) -> Offset:
        if popup_height < 1:
            popup_height = 1
        if popup_width < 1:
            popup_width = 1

        below_y = cursor_offset.y + 1
        above_y = cursor_offset.y - popup_height

        if below_y + popup_height <= screen_size.height:
            y = below_y
        elif above_y >= 0:
            y = above_y
        else:
            y = max(0, min(below_y, screen_size.height - popup_height))

        anchor_x = cursor_offset.x - 2
        max_x = max(0, screen_size.width - popup_width)
        x = min(max(anchor_x, 0), max_x)
        return Offset(x, y)

    def _render_content(self, lines: list[str] | None = None) -> None:
        if lines is None:
            if not self._current_suggestions:
                return

            raw_lines = [item.display_text for item in self._current_suggestions]

            width = self.styles.width
            if width and hasattr(width, 'value'):
                 popup_width = int(width.value)
            else:
                 popup_width = 20

            available_width = max(1, popup_width - 2)
            lines = [line[:available_width] for line in raw_lines]

        rendered = Text()
        for index, line in enumerate(lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == self._selected_index else ""
            rendered.append(line, style=style)

        self.update(rendered)
