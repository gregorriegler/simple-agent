import asyncio
from typing import Optional, List, Any

from textual import events
from textual.widgets import TextArea
from textual.geometry import Offset

from simple_agent.infrastructure.textual.widgets.autocomplete_popup import AutocompletePopup
from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    AutocompleteRequest
)

class AutocompleteController:
    """
    Manages autocomplete logic for a TextArea.
    """
    def __init__(self, text_area: TextArea, popup: AutocompletePopup, autocompleters: List[Autocompleter]):
        self.text_area = text_area
        self.popup = popup
        self.autocompleters = autocompleters

        self._visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._anchor_x: Optional[int] = None
        self._active_autocompleter: Optional[Autocompleter] = None
        self._active_request: Optional[AutocompleteRequest] = None

        # Track files referenced via autocomplete
        self.referenced_files: set[str] = set()

    def set_autocompleters(self, autocompleters: List[Autocompleter]):
        self.autocompleters = autocompleters

    def clear_referenced_files(self):
        self.referenced_files.clear()

    async def handle_key(self, event: events.Key) -> bool:
        """
        Handle key events for autocomplete navigation and selection.
        Returns True if the event was handled, False otherwise.
        """
        if not self._visible:
            return False

        if event.key == "tab":
            self._complete_selection()
            return True

        if event.key in ("down", "up"):
            self._navigate(event.key)
            return True

        if event.key == "escape":
            self.hide()
            return True

        if event.key == "enter":
            self._complete_selection()
            return True

        return False

    def check_autocomplete(self) -> None:
        """Check if we should show autocomplete based on current text."""
        cursor_location = self.text_area.cursor_location
        row, col = cursor_location
        try:
            line = self.text_area.document.get_line(row)
        except IndexError:
            self.hide()
            return

        for autocompleter in self.autocompleters:
            request = autocompleter.check(row, col, line)
            if request:
                self._active_autocompleter = autocompleter
                self._active_request = request
                asyncio.create_task(self._fetch_suggestions(autocompleter, request))
                return

        self.hide()

    async def _fetch_suggestions(self, autocompleter: Autocompleter, request: AutocompleteRequest):
        if self._active_autocompleter != autocompleter or self._active_request != request:
            return

        suggestions = await autocompleter.get_suggestions(request)

        if self._active_autocompleter == autocompleter and self._active_request == request:
            if suggestions:
                self._display_suggestions(suggestions)
            else:
                self.hide()

    def _display_suggestions(self, suggestions: list) -> None:
        was_visible = self._visible
        self._visible = True
        self._current_suggestions = suggestions
        self._selected_index = 0

        if not was_visible:
            self._anchor_x = self.text_area.cursor_screen_offset.x

        self._update_display()

    def hide(self) -> None:
        """Hide autocomplete suggestions."""
        self._visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._anchor_x = None
        self._active_autocompleter = None
        self._active_request = None
        self._update_display()

    def _navigate(self, direction: str) -> None:
        """Navigate autocomplete suggestions with arrow keys."""
        if not self._current_suggestions:
            return

        if direction == "down":
            self._selected_index = (self._selected_index + 1) % len(self._current_suggestions)
        elif direction == "up":
            self._selected_index = (self._selected_index - 1) % len(self._current_suggestions)

        self._update_display()

    def _complete_selection(self) -> None:
        """Complete the selected item."""
        if not self._current_suggestions or self._selected_index >= len(self._current_suggestions):
            return

        if not self._active_autocompleter or not self._active_request:
            return

        selected = self._current_suggestions[self._selected_index]
        row, col = self.text_area.cursor_location

        completion_result = self._active_autocompleter.get_completion(selected)

        start_col = self._active_request.start_index
        self.text_area.replace(
            completion_result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        if completion_result.attachments:
            self.referenced_files.update(completion_result.attachments)

        self.hide()

    def _update_display(self) -> None:
        """Update the autocomplete display in the popup."""
        popup = self.popup
        if not popup:
            return

        if self._visible and self._current_suggestions and self._active_autocompleter:
            lines = [
                self._active_autocompleter.format_suggestion(item)
                for item in self._current_suggestions
            ]

            if self._anchor_x is not None:
                target_x = self._anchor_x
            else:
                target_x = self.text_area.cursor_screen_offset.x

            target_offset = Offset(target_x, self.text_area.cursor_screen_offset.y)

            # Using self.text_area.app.screen.size because popup relies on screen size
            screen_size = self.text_area.app.screen.size

            popup.show_suggestions(
                lines=lines,
                selected_index=self._selected_index,
                cursor_offset=target_offset,
                screen_size=screen_size,
            )
        else:
            popup.hide()
