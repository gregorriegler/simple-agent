import logging
from typing import Optional

from textual import events
from textual.message import Message
from textual.widgets import TextArea

from simple_agent.infrastructure.textual.widgets.autocomplete_popup import AutocompletePopup
from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    SlashCommandAutocompleter,
    FileSearchAutocompleter,
)
from simple_agent.infrastructure.textual.widgets.file_context_expander import FileContextExpander
from simple_agent.infrastructure.textual.widgets.autocomplete_controller import AutocompleteController

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
        self._slash_command_registry = None
        self._file_searcher = None

        self.autocompleters: list[Autocompleter] = autocompleters if autocompleters is not None else []
        self._popup: AutocompletePopup | None = None

        # Delegates
        self.expander = FileContextExpander()
        self.controller: AutocompleteController | None = None

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
        self.autocompleters.clear()
        if self._slash_command_registry:
            self.autocompleters.append(SlashCommandAutocompleter(self._slash_command_registry))
        if self._file_searcher:
            self.autocompleters.append(FileSearchAutocompleter(self._file_searcher))

        if self.controller:
            self.controller.set_autocompleters(self.autocompleters)

    def on_mount(self) -> None:
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

        # Initialize and mount popup
        self._popup = AutocompletePopup(id="autocomplete-popup")
        self.mount(self._popup)

        # Initialize controller
        self.controller = AutocompleteController(self, self._popup, self.autocompleters)

    def get_referenced_files(self) -> set[str]:
        """Return the set of files that were selected via autocomplete and are still in the text."""
        if not self.controller:
            return set()

        current_text = self.text
        # Filter references that are still present in the text
        return {f for f in self.controller.referenced_files if f"[📦{f}]" in current_text}

    def submit(self) -> None:
        """Submit the current text."""
        content = self.text.strip()
        referenced_files = self.get_referenced_files()

        # Expand file content
        content = self.expander.expand(content, referenced_files)

        # Emit the fully processed content
        self.post_message(self.Submitted(content))

        self.clear()
        if self.controller:
            self.controller.clear_referenced_files()
            self.controller.hide()

    async def _on_key(self, event: events.Key) -> None:
        if self.controller:
            if await self.controller.handle_key(event):
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
