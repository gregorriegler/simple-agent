import asyncio
import logging
from typing import Optional

from rich.text import Text
from textual import events
from textual.message import Message
from textual.widgets import TextArea

from simple_agent.infrastructure.textual.widgets.autocomplete_popup import AutocompletePopup
from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    SlashCommandAutocompleter,
    FileSearchAutocompleter,
    CompletionResult
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
        autocompleters: list[Autocompleter] | None = None,
        id: str | None = None,
        **kwargs
    ):
        super().__init__(id=id, **kwargs)

        # State for configuration
        self._slash_command_registry = None
        self._file_searcher = None

        # Initial autocompleters config
        self._initial_autocompleters = autocompleters or []

        # Internal components
        self.popup: AutocompletePopup | None = None
        self.expander = FileContextExpander()

        # Track referenced files
        self._referenced_files: set[str] = set()

    @property
    def slash_command_registry(self):
        return self._slash_command_registry

    @slash_command_registry.setter
    def slash_command_registry(self, value):
        self._slash_command_registry = value
        self._update_popup_config()

    @property
    def file_searcher(self):
        return self._file_searcher

    @file_searcher.setter
    def file_searcher(self, value):
        self._file_searcher = value
        self._update_popup_config()

    def _update_popup_config(self):
        if not self.popup:
            return

        autocompleters = list(self._initial_autocompleters)
        if self._slash_command_registry:
            autocompleters.append(SlashCommandAutocompleter(self._slash_command_registry))
        if self._file_searcher:
            autocompleters.append(FileSearchAutocompleter(self._file_searcher))

        self.popup.autocompleters = autocompleters

    def on_mount(self) -> None:
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

        # Initialize and mount popup
        self.popup = AutocompletePopup(id="autocomplete-popup")
        self.mount(self.popup)

        # Trigger update to pick up any registries set before mount
        self._update_popup_config()

    def get_referenced_files(self) -> set[str]:
        """Return the set of files that were selected via autocomplete and are still in the text."""
        current_text = self.text
        return {f for f in self._referenced_files if f"[📦{f}]" in current_text}

    def submit(self) -> None:
        """Submit the current text."""
        # Expand file contexts
        expanded_content = self.expander.expand(self.text, self._referenced_files)

        # Emit the fully processed content
        self.post_message(self.Submitted(expanded_content))

        self.clear()
        self._referenced_files.clear()
        if self.popup:
            self.popup.hide()

    async def _on_key(self, event: events.Key) -> None:
        # Delegate key handling to popup first
        # We need to await it because handle_key might need to be async or just return result
        if self.popup:
            result = await self.popup.handle_key(event.key)
            if isinstance(result, CompletionResult):
                self._apply_completion(result)
                event.stop()
                event.prevent_default()
                return
            elif result is True:
                # Key handled by popup (e.g. navigation)
                event.stop()
                event.prevent_default()
                return

        # Let Enter submit the form
        if event.key == "enter":
            self.submit()
            event.stop()
            event.prevent_default()
            return

        # ctrl+j is how Windows/mintty sends Ctrl+Enter - insert newline
        if event.key in ("ctrl+enter", "ctrl+j"):
            self.insert("\n")
            event.stop()
            event.prevent_default()
            return

        # IMPORTANT: Call super()._on_key() first to let the character be inserted
        await super()._on_key(event)

        # THEN check for autocomplete
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

        self.popup.check(row, col, line, self.cursor_screen_offset, self.app.screen.size)

    def _apply_completion(self, result: CompletionResult) -> None:
        row, col = self.cursor_location

        # Use start_offset populated by the popup logic
        start_col = result.start_offset if result.start_offset is not None else 0

        self.replace(
            result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        if result.attachments:
            self._referenced_files.update(result.attachments)
