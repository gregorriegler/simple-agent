import asyncio
from typing import Any, Optional
from textual.widgets import Static
from textual.geometry import Offset, Size
from rich.text import Text

from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    AutocompleteRequest,
    CompletionResult
)


def calculate_autocomplete_position(
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
        super().__init__(**kwargs)
        self.autocompleters = autocompleters or []

        # State
        self._current_suggestions: list[Any] = []
        self._selected_index: int = 0
        self._active_autocompleter: Autocompleter | None = None
        self._active_request: AutocompleteRequest | None = None
        self._anchor_x: int | None = None

    async def handle_key(self, key: str) -> bool | CompletionResult:
        """
        Handle a key press.
        Returns:
            - CompletionResult if a suggestion was selected.
            - True if the key was consumed (handled).
            - False if the key should propagate.
        """
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

    def check(self, row: int, col: int, line: str, cursor_screen_offset: Offset, screen_size: Size) -> None:
        """Check for autocomplete triggers and fetch suggestions if needed."""
        for autocompleter in self.autocompleters:
            request = autocompleter.check(row, col, line)
            if request:
                self._active_autocompleter = autocompleter
                self._active_request = request
                asyncio.create_task(self._fetch_suggestions(autocompleter, request, cursor_screen_offset, screen_size))
                return

        self.hide()

    def hide(self) -> None:
        self.display = False
        self._current_suggestions = []
        self._selected_index = 0
        self._anchor_x = None
        self._active_autocompleter = None
        self._active_request = None

    async def _fetch_suggestions(
        self,
        autocompleter: Autocompleter,
        request: AutocompleteRequest,
        cursor_screen_offset: Offset,
        screen_size: Size
    ) -> None:
        if self._active_autocompleter != autocompleter or self._active_request != request:
            return

        suggestions = await autocompleter.get_suggestions(request)

        if self._active_autocompleter == autocompleter and self._active_request == request:
            if suggestions:
                self._show_suggestions(suggestions, cursor_screen_offset, screen_size)
            else:
                self.hide()

    def _show_suggestions(
        self,
        suggestions: list[Any],
        cursor_offset: Offset,
        screen_size: Size,
    ) -> None:
        was_visible = self.display
        self._current_suggestions = suggestions
        self._selected_index = 0
        self.display = True

        if not was_visible:
            # Anchor popup X position to current cursor screen position
            self._anchor_x = cursor_offset.x

        self._update_display(cursor_offset, screen_size)

    def _navigate(self, direction: str) -> None:
        if not self._current_suggestions:
            return

        if direction == "down":
            self._selected_index = (self._selected_index + 1) % len(self._current_suggestions)
        elif direction == "up":
            self._selected_index = (self._selected_index - 1) % len(self._current_suggestions)

        # We need screen info to update display, but we don't store it.
        # However, for navigation, the position shouldn't change drastically usually,
        # but we do need to re-render.
        # We can either store the last render position or just re-render content.
        # Ideally we pass screen info, but handle_key doesn't have it.
        # Let's try to just update the content without moving the window if possible,
        # but `_update_display` calls `calculate_autocomplete_position`.

        # Workaround: Use self.screen.size if available (it is available on mounted widgets)
        screen_size = self.screen.size
        # For cursor offset, we use the last known position or current widget position?
        # Using self.absolute_offset is weird because it's the result.
        # Let's approximate or reuse stored anchors if we had them.
        # Better yet, since we are just changing selection, we don't strictly need to move the popup
        # if the text didn't change. But we do need to re-render the highlighting.

        self._render_content()

    def _get_selection(self) -> CompletionResult | None:
        if not self._current_suggestions or self._selected_index >= len(self._current_suggestions):
            return None

        if not self._active_autocompleter or not self._active_request:
            return None

        selected = self._current_suggestions[self._selected_index]
        autocompleter = self._active_autocompleter
        start_offset = self._active_request.start_index

        self.hide()

        result = autocompleter.get_completion(selected)
        result.start_offset = start_offset
        return result

    def _update_display(self, cursor_offset: Offset, screen_size: Size) -> None:
        lines = [
            self._active_autocompleter.format_suggestion(item)
            for item in self._current_suggestions
        ]

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

        # Use anchored X if set
        if self._anchor_x is not None:
            target_x = self._anchor_x
        else:
            target_x = cursor_offset.x

        target_offset = Offset(target_x, cursor_offset.y)

        self.absolute_offset = calculate_autocomplete_position(
            cursor_offset=target_offset,
            screen_size=screen_size,
            popup_height=popup_height,
            popup_width=popup_width,
        )

        self._render_content(trimmed_lines)

    def _render_content(self, lines: list[str] | None = None) -> None:
        # Re-generate lines if not provided (e.g. navigation)
        if lines is None:
            if not self._active_autocompleter or not self._current_suggestions:
                return

            # Recalculate trimmed lines - this repeats some logic but is safer
            # We assume width/height is already set correctly by _update_display
            raw_lines = [
                self._active_autocompleter.format_suggestion(item)
                for item in self._current_suggestions
            ]
            # Use current style width for trimming
            # self.styles.width might be a scalar or None.
            # Safer to rely on what we computed before.
            # For simplicity, let's just re-trim based on loose constraints or store trimmed lines?
            # Storing trimmed lines is cleaner.

            # Let's just grab the width from styles if possible, or recompute.
            # Since we are inside a widget, self.size.width might be valid if layout happened?
            # But Textual layout is async.

            # Let's simpler approach: Re-use logic from _update_display but without moving window.
            # We need available_width.
            # If we don't have it, we might render incorrectly.
            # But wait, `_update_display` is called when showing. `_navigate` is called when already shown.

            width = self.styles.width
            if width and hasattr(width, 'value'):
                 popup_width = int(width.value)
            else:
                 popup_width = 20 # Fallback

            available_width = max(1, popup_width - 2)
            lines = [line[:available_width] for line in raw_lines]

        rendered = Text()
        for index, line in enumerate(lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == self._selected_index else ""
            rendered.append(line, style=style)

        self.update(rendered)
