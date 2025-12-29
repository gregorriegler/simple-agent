import asyncio
import logging
from typing import Optional

from textual import events
from textual.geometry import Offset
from textual.message import Message
from textual.widgets import Static, TextArea
from textual.css.query import NoMatches

from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    AutocompleteRequest
)
from simple_agent.infrastructure.textual.widgets.autocomplete_popup import AutocompletePopup

logger = logging.getLogger(__name__)

class SubmittableTextArea(TextArea):
    class Submitted(Message):
        def __init__(self, value: str, referenced_files: set[str]):
            self.value = value
            self.referenced_files = referenced_files
            super().__init__()

    def __init__(
        self,
        autocompleters: list[Autocompleter] | None = None,
        popup: AutocompletePopup | None = None,
        hint_widget: Static | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x = None

        self.autocompleters: list[Autocompleter] = autocompleters if autocompleters is not None else []
        self._popup = popup
        self._hint_widget = hint_widget
        self._active_autocompleter: Autocompleter | None = None
        self._active_request: AutocompleteRequest | None = None

        self._referenced_files: set[str] = set()

    def get_referenced_files(self) -> set[str]:
        """Return the set of files that were selected via autocomplete and are still in the text."""
        current_text = self.text
        return {f for f in self._referenced_files if f"[📦{f}]" in current_text}

    def submit(self) -> None:
        """Submit the current text."""
        content = self.text.strip()
        referenced_files = self.get_referenced_files()

        self.post_message(self.Submitted(content, referenced_files))

        self.clear()
        self._referenced_files.clear()
        self._hide_autocomplete()

    async def _on_key(self, event: events.Key) -> None:
        # Handle Tab for autocomplete
        if event.key == "tab" and self._autocomplete_visible:
            self._complete_selection()
            event.stop()
            event.prevent_default()
            return

        # Handle arrow keys for autocomplete navigation
        if event.key in ("down", "up") and self._autocomplete_visible:
            self._navigate_autocomplete(event.key)
            event.stop()
            event.prevent_default()
            return

        # Handle escape to close autocomplete
        if event.key == "escape" and self._autocomplete_visible:
            self._hide_autocomplete()
            event.stop()
            event.prevent_default()
            return

        # Let Enter submit the form
        if event.key == "enter":
            if self._autocomplete_visible:
                self._complete_selection()
                event.stop()
                event.prevent_default()
                return

            self.submit()
            event.stop()
            event.prevent_default()
            return
        # ctrl+j is how Windows/mintty sends Ctrl+Enter - insert newline
        if event.key in ("ctrl+enter", "ctrl+j"):
            # Explicitly insert newline
            self.insert("\n")
            event.stop()
            event.prevent_default()
            return

        # IMPORTANT: Call super()._on_key() first to let the character be inserted
        await super()._on_key(event)

        # THEN check for autocomplete (now self.text will include the new character)
        self.call_after_refresh(self._check_autocomplete)

    def _check_autocomplete(self) -> None:
        """Check if we should show autocomplete based on current text."""
        cursor_location = self.cursor_location
        row, col = cursor_location
        try:
            line = self.document.get_line(row)
        except IndexError:
            self._hide_autocomplete()
            return

        for autocompleter in self.autocompleters:
            request = autocompleter.check(row, col, line)
            if request:
                self._active_autocompleter = autocompleter
                self._active_request = request
                asyncio.create_task(self._fetch_suggestions(autocompleter, request))
                return

        self._hide_autocomplete()

    async def _fetch_suggestions(self, autocompleter: Autocompleter, request: AutocompleteRequest):
        # Double check if we are still on the same request (async race condition)
        if self._active_autocompleter != autocompleter or self._active_request != request:
            return

        suggestions = await autocompleter.get_suggestions(request)

        # Verify again before displaying
        if self._active_autocompleter == autocompleter and self._active_request == request:
            if suggestions:
                self._display_suggestions(suggestions)
            else:
                self._hide_autocomplete()

    def _display_suggestions(self, suggestions: list) -> None:
        was_visible = self._autocomplete_visible
        self._autocomplete_visible = True
        self._current_suggestions = suggestions
        self._selected_index = 0

        if not was_visible:
            self._autocomplete_anchor_x = self.cursor_screen_offset.x

        self._update_autocomplete_display()

    def _hide_autocomplete(self) -> None:
        """Hide autocomplete suggestions."""
        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x = None
        self._active_autocompleter = None
        self._active_request = None
        self._update_autocomplete_display()

    def _navigate_autocomplete(self, direction: str) -> None:
        """Navigate autocomplete suggestions with arrow keys."""
        if not self._current_suggestions:
            return

        if direction == "down":
            self._selected_index = (self._selected_index + 1) % len(self._current_suggestions)
        elif direction == "up":
            self._selected_index = (self._selected_index - 1) % len(self._current_suggestions)

        self._update_autocomplete_display()

    def _complete_selection(self) -> None:
        """Complete the selected item."""
        if not self._current_suggestions or self._selected_index >= len(self._current_suggestions):
            return

        if not self._active_autocompleter or not self._active_request:
            return

        selected = self._current_suggestions[self._selected_index]
        row, col = self.cursor_location

        completion_result = self._active_autocompleter.get_completion(selected)

        # Apply the completion
        start_col = self._active_request.start_index
        # Replace from start of trigger/word to current cursor position
        self.replace(
            completion_result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        # Add attachments
        if completion_result.attachments:
            self._referenced_files.update(completion_result.attachments)

        self._hide_autocomplete()

    def _update_autocomplete_display(self) -> None:
        """Update the autocomplete display in the popup."""
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
                    target_x = self.cursor_screen_offset.x

                target_offset = Offset(target_x, self.cursor_screen_offset.y)

                popup.show_suggestions(
                    lines=lines,
                    selected_index=self._selected_index,
                    cursor_offset=target_offset,
                    screen_size=self.app.screen.size,
                )
        elif popup:
            popup.hide()

        if self._hint_widget:
            self._hint_widget.update("Enter to submit, Ctrl+Enter for newline")
