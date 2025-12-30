import asyncio
import logging
from typing import Optional

from rich.text import Text
from textual import events
from textual.message import Message
from textual.widgets import TextArea
from textual.geometry import Offset

from simple_agent.infrastructure.textual.widgets.autocomplete_popup import (
    AutocompletePopup,
    CaretScreenLocation,
    PopupAnchor,
)
from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    NullAutocompleter,
    CompletionResult,
    CompletionSearch,
    CursorAndLine,
    MessageDraft,
    Suggestion,
)
from simple_agent.infrastructure.textual.widgets.file_context_expander import FileContextExpander

logger = logging.getLogger(__name__)

class SmartInput(TextArea):
    """
    A unified SmartInput widget that combines text editing, autocomplete, and file context handling.
    Inherits from TextArea to provide the editing surface, but manages its own Popup and Hint.
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
        self._active_search: CompletionSearch | None = None

    def on_mount(self) -> None:
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

        # AutocompletePopup is now a dumb view, doesn't need autocompleter
        self.popup = AutocompletePopup(id="autocomplete-popup")
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
        self._active_search = None

    async def _on_key(self, event: events.Key) -> None:
        if self.popup and self.popup.display:
            result = await self.popup.handle_key(event.key)
            if isinstance(result, CompletionResult):
                self._apply_completion(result)
                event.stop()
                event.prevent_default()
                return
            elif result is True:
                # Key handled by popup (e.g. navigation), prevent default behavior
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
            self._active_search = None
            return

        cursor_and_line = CursorAndLine(row, col, line)

        # Check autocompleter directly
        search = self.autocompleter.check(cursor_and_line)

        if search.is_triggered():
            self._active_search = search

            # Create Anchor
            caret_location = CaretScreenLocation(
                offset=self.cursor_screen_offset,
                screen_size=self.app.screen.size
            )
            anchor = caret_location.anchor_to_word(cursor_and_line)

            asyncio.create_task(self._fetch_suggestions(search, anchor))
        else:
            self.popup.hide()
            self._active_search = None

    async def _fetch_suggestions(self, search: CompletionSearch, anchor: PopupAnchor) -> None:
        if self._active_search is not search:
            return

        suggestions = await search.get_suggestions()

        if self._active_search is search:
            if suggestions:
                if self.popup:
                    self.popup.show(suggestions, anchor)
            else:
                if self.popup:
                    self.popup.hide()

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
