import asyncio
import logging
from pathlib import Path

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.css.query import NoMatches
from textual.geometry import Offset, Size
from textual.message import Message
from textual.widgets import Static, TextArea
from textual.widget import Widget

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.file_search import FileSearcher
from simple_agent.infrastructure.textual.widgets.autocomplete_popup import AutocompletePopup, calculate_autocomplete_position
from simple_agent.infrastructure.textual.autocompletion import (
    Autocompleter,
    SlashCommandAutocompleter,
    FileSearchAutocompleter,
    AutocompleteRequest
)
from simple_agent.infrastructure.textual.widgets.submittable_text_area import SubmittableTextArea

logger = logging.getLogger(__name__)


class SmartInput(Widget):
    class Submitted(Message):
        def __init__(self, value: str):
            self.value = value
            super().__init__()

    DEFAULT_CSS = """
    SmartInput {
        height: auto;
        dock: bottom;
    }
    """

    def __init__(self, id: str | None = None):
        super().__init__(id=id)
        self._slash_command_registry = None
        self._file_searcher = None
        self._autocompleters = []

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
        self._autocompleters.clear()
        if self._slash_command_registry:
            self._autocompleters.append(SlashCommandAutocompleter(self._slash_command_registry))
        if self._file_searcher:
            self._autocompleters.append(FileSearchAutocompleter(self._file_searcher))

    def compose(self) -> ComposeResult:
        hint = Static("Enter to submit, Ctrl+Enter for newline", id="input-hint")
        popup = AutocompletePopup(id="autocomplete-popup")
        text_area = SubmittableTextArea(
            autocompleters=self._autocompleters,
            popup=popup,
            hint_widget=hint,
            id="user-input"
        )
        yield hint
        yield text_area
        yield popup

    def submit(self) -> None:
        try:
            text_area = self.query_one("#user-input", SubmittableTextArea)
        except NoMatches:
            return

        content = text_area.text.strip()

        referenced_files = text_area.get_referenced_files()
        if referenced_files:
            file_contents = []
            for file_path_str in referenced_files:
                try:
                    path = Path(file_path_str)
                    if path.exists() and path.is_file():
                        file_text = path.read_text(encoding="utf-8")
                        file_contents.append(f'<file_context path="{file_path_str}">\n{file_text}\n</file_context>')
                except Exception as e:
                    logger.error(f"Failed to read referenced file {file_path_str}: {e}")

            if file_contents:
                content += "\n" + "\n".join(file_contents)
                # Clear references after consuming them
                text_area._referenced_files.clear()

        self.post_message(self.Submitted(content))

        text_area.clear()
        text_area._hide_autocomplete()
