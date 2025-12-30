import asyncio
import logging
from typing import Optional

from rich.text import Text
from textual import events
from textual.message import Message
from textual.widgets import TextArea
from textual.geometry import Offset

from simple_agent.infrastructure.textual.widgets.autocomplete_popup import AutocompletePopup
from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    NullAutocompleter,
    CompletionResult,
    CursorAndLine,
    MessageDraft,
    PopupAnchor,
)
from simple_agent.infrastructure.textual.widgets.file_context_expander import FileContextExpander

logger = logging.getLogger(__name__)

class SmartInput(TextArea):
    """
    A unified SmartInput widget that combines text editing, autocomplete, and file context handling.
    Inherits from TextArea to provide the editing surface, but manages its own Popup and Hint.

    Delegates autocomplete logic to AutocompletePopup (which acts as a smart component).
    Delegates file context expansion to FileContextExpander.
    """

    class Submitted(Message):
        def __init__(self, value: str):
            self.value = value
            super().__init__()

    DEFAULT_CSS = """
    SmartInput {
        height: auto;
        dock: bottom;
        border: solid $primary;
    }
    """

    def __init__(
        self,
        autocompleter: Autocompleter = NullAutocompleter(),
        id: str | None = None,
        **kwargs
    ):
        super().__init__(id=id, **kwargs)

        self.autocompleter = autocompleter
        self.popup: AutocompletePopup | None = None
        self.expander = FileContextExpander()

        self._referenced_files: set[str] = set()

    def on_mount(self) -> None:
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

        self.popup = AutocompletePopup(autocompleter=self.autocompleter, id="autocomplete-popup")
        self.mount(self.popup)

    def get_referenced_files(self) -> set[str]:
        """Return the set of files that were selected via autocomplete and are still in the text."""
        return MessageDraft(self.text, self._referenced_files).active_files

    def submit(self) -> None:
        """Submit the current text."""
        draft = MessageDraft(self.text, self._referenced_files)
        expanded_content = self.expander.expand(draft)

        self.post_message(self.Submitted(expanded_content))

        self.clear()
        self._referenced_files.clear()
        if self.popup:
            self.popup.hide()

    async def _on_key(self, event: events.Key) -> None:
        if self.popup:
            result = await self.popup.handle_key(event.key)
            if isinstance(result, CompletionResult):
                self._apply_completion(result)
                event.stop()
                event.prevent_default()
                return
            elif result is True:
                event.stop()
                event.prevent_default()
                return

        if event.key == "enter":
            self.submit()
            event.stop()
            event.prevent_default()
            return

        if event.key in ("ctrl+enter", "ctrl+j"):
            self.insert("\n")
            event.stop()
            event.prevent_default()
            return

        await super()._on_key(event)

        if self.popup:
            self.call_after_refresh(self._trigger_autocomplete_check)

    def _trigger_autocomplete_check(self) -> None:
        """Helper to call popup check with current context."""
        if not self.popup:
            return

        row, col = self.cursor_location
        try:
            line = self.document.get_line(row)
        except IndexError:
            self.popup.hide()
            return

        cursor_and_line = CursorAndLine(row, col, line)

        anchor = PopupAnchor.from_cursor_context(
            cursor_and_line,
            self.cursor_screen_offset,
            self.app.screen.size
        )

        self.popup.check(cursor_and_line, anchor)

    def _apply_completion(self, result: CompletionResult) -> None:
        row, col = self.cursor_location

        start_col = result.start_offset if result.start_offset is not None else 0

        self.replace(
            result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        if result.attachments:
            self._referenced_files.update(result.attachments)
