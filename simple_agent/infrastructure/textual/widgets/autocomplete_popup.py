import asyncio
from dataclasses import dataclass
from typing import Any, Optional
from textual.widgets import Static
from textual.geometry import Offset, Size
from rich.text import Text

from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    CompletionSearch,
    CompletionResult,
    Suggestion,
    CursorAndLine,
    PopupAnchor
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

    def check(self, cursor_and_line: CursorAndLine, anchor: "PopupAnchor") -> None:
        search = self.autocompleter.check(cursor_and_line)
        # Even if search is NoOpSearch (not triggered), calling get_suggestions handles it (returns empty).
        # However, we want to know if we should potentially show something.
        # If not triggered, we should hide.
        if search.is_triggered():
            self._active_search = search
            asyncio.create_task(self._fetch_suggestions(search, anchor))
        else:
            self.hide()

    def hide(self) -> None:
        self.display = False
        self._current_suggestions = []
        self._selected_index = 0
        self._active_search = None

    async def _fetch_suggestions(
        self,
        search: CompletionSearch,
        anchor: PopupAnchor
    ) -> None:
        # Check if the search is still active (identity check)
        if self._active_search is not search:
            return

        suggestions = await search.get_suggestions()

        # Check again after await
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
        self._current_suggestions = suggestions
        self._selected_index = 0
        self.display = True

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

        # No need to check _active_search strictly here if we trust the display state,
        # but it's good practice.
        if not self._active_search:
            return None

        selected = self._current_suggestions[self._selected_index]
        self.hide()

        # The Suggestion now encapsulates the logic to create a full CompletionResult,
        # including the start_offset which was injected when the Suggestion was created.
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

        self.absolute_offset = anchor.get_placement(Size(popup_width, popup_height))

        self._render_content(trimmed_lines)

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
