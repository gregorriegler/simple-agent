import asyncio
import logging
from typing import Optional

from textual import events
from textual.geometry import Offset
from textual.widgets import TextArea
from textual.widget import Widget

from simple_agent.infrastructure.textual.widgets.autocomplete_popup import AutocompletePopup
from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    AutocompleteRequest
)

logger = logging.getLogger(__name__)

class AutocompleteController:
    """
    Manages the autocomplete logic for a SmartInput widget.
    It coordinates between the input widget (TextArea), the popup, and the list of autocompleters.
    """
    def __init__(
        self,
        owner: TextArea,
        popup: AutocompletePopup,
        autocompleters: list[Autocompleter] | None = None
    ):
        self._owner = owner
        self._popup = popup
        self.autocompleters: list[Autocompleter] = autocompleters if autocompleters is not None else []

        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x: Optional[int] = None
        self._active_autocompleter: Autocompleter | None = None
        self._active_request: AutocompleteRequest | None = None

    @property
    def is_visible(self) -> bool:
        return self._autocomplete_visible

    async def handle_key(self, event: events.Key) -> bool:
        """
        Handle a key event. Returns True if the event was handled by autocomplete,
        False otherwise.
        """
        if not self._autocomplete_visible:
            return False

        if event.key == "tab":
            self._complete_selection()
            return True

        if event.key == "down":
            self._navigate("down")
            return True

        if event.key == "up":
            self._navigate("up")
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
        cursor_location = self._owner.cursor_location
        row, col = cursor_location
        try:
            line = self._owner.document.get_line(row)
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

    def hide(self) -> None:
        """Hide autocomplete suggestions."""
        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x = None
        self._active_autocompleter = None
        self._active_request = None
        self._update_display()

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
        was_visible = self._autocomplete_visible
        self._autocomplete_visible = True
        self._current_suggestions = suggestions
        self._selected_index = 0

        if not was_visible:
            # Anchor popup X position to current cursor screen position
            self._autocomplete_anchor_x = self._owner.cursor_screen_offset.x

        self._update_display()

    def _navigate(self, direction: str) -> None:
        if not self._current_suggestions:
            return

        if direction == "down":
            self._selected_index = (self._selected_index + 1) % len(self._current_suggestions)
        elif direction == "up":
            self._selected_index = (self._selected_index - 1) % len(self._current_suggestions)

        self._update_display()

    def _complete_selection(self) -> None:
        if not self._current_suggestions or self._selected_index >= len(self._current_suggestions):
            return

        if not self._active_autocompleter or not self._active_request:
            return

        selected = self._current_suggestions[self._selected_index]
        row, col = self._owner.cursor_location

        completion_result = self._active_autocompleter.get_completion(selected)

        start_col = self._active_request.start_index

        # Replace text in owner
        self._owner.replace(
            completion_result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        # Notify owner of attachments if possible
        if hasattr(self._owner, "_referenced_files") and completion_result.attachments:
            self._owner._referenced_files.update(completion_result.attachments)

        self.hide()

    def _update_display(self) -> None:
        popup = self._popup

        if self._autocomplete_visible and self._current_suggestions and self._active_autocompleter:
            lines = [
                self._active_autocompleter.format_suggestion(item)
                for item in self._current_suggestions
            ]

            if popup:
                if self._autocomplete_anchor_x is not None:
                    target_x = self._autocomplete_anchor_x
                else:
                    target_x = self._owner.cursor_screen_offset.x

                target_offset = Offset(target_x, self._owner.cursor_screen_offset.y)

                popup.show_suggestions(
                    lines=lines,
                    selected_index=self._selected_index,
                    cursor_offset=target_offset,
                    screen_size=self._owner.app.screen.size,
                )
        elif popup:
            popup.hide()
