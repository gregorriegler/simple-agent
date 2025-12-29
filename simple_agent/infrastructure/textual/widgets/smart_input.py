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
)
from simple_agent.infrastructure.textual.widgets.autocomplete_controller import AutocompleteController
from simple_agent.infrastructure.textual.widgets.file_context_expander import FileContextExpander

logger = logging.getLogger(__name__)

class SmartInput(TextArea):
    """
    A unified SmartInput widget that combines text editing, autocomplete, and file context handling.
    Inherits from TextArea to provide the editing surface, but manages its own Popup and Hint.

    Delegates autocomplete logic to AutocompleteController.
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
        /* Ensure it behaves like a TextArea visually */
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

        # Initial autocompleters
        self._initial_autocompleters = autocompleters if autocompleters is not None else []

        # Internal components
        self._popup: AutocompletePopup | None = None
        self.controller: AutocompleteController | None = None
        self.expander = FileContextExpander()

        # Track referenced files
        self._referenced_files: set[str] = set()

    @property
    def slash_command_registry(self):
        return self._slash_command_registry

    @slash_command_registry.setter
    def slash_command_registry(self, value):
        self._slash_command_registry = value
        self._rebuild_autocompleters()

    @property
    def file_searcher(self):
        return self._file_searcher

    @file_searcher.setter
    def file_searcher(self, value):
        self._file_searcher = value
        self._rebuild_autocompleters()

    def _rebuild_autocompleters(self):
        if not self.controller:
            return

        autocompleters = list(self._initial_autocompleters) # Start with base ones
        if self._slash_command_registry:
            autocompleters.append(SlashCommandAutocompleter(self._slash_command_registry))
        if self._file_searcher:
            autocompleters.append(FileSearchAutocompleter(self._file_searcher))

        self.controller.autocompleters = autocompleters

    def on_mount(self) -> None:
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

        # Initialize and mount popup
        self._popup = AutocompletePopup(id="autocomplete-popup")
        self.mount(self._popup)

        # Initialize controller
        self.controller = AutocompleteController(
            owner=self,
            popup=self._popup,
            autocompleters=self._initial_autocompleters
        )

        # Trigger rebuild to pick up any registries set before mount
        self._rebuild_autocompleters()

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
        if self.controller:
            self.controller.hide()

    async def _on_key(self, event: events.Key) -> None:
        # Delegate key handling to controller first
        if self.controller and await self.controller.handle_key(event):
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
            # Explicitly insert newline
            self.insert("\n")
            event.stop()
            event.prevent_default()
            return

        # IMPORTANT: Call super()._on_key() first to let the character be inserted
        await super()._on_key(event)

        # THEN check for autocomplete (now self.text will include the new character)
        if self.controller:
            self.call_after_refresh(self.controller.check_autocomplete)
