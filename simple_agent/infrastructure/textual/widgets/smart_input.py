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
from simple_agent.infrastructure.textual.autocomplete_strategies import (
    AutocompleteStrategy,
    SlashCommandStrategy,
    FileSearchStrategy,
    CompletionContext
)

logger = logging.getLogger(__name__)


class SubmittableTextArea(TextArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._slash_command_registry: SlashCommandRegistry | None = None
        self._file_searcher: FileSearcher | None = None
        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x = None

        # New strategy state
        self.strategies: list[AutocompleteStrategy] = []
        self._active_strategy: AutocompleteStrategy | None = None
        self._active_context: CompletionContext | None = None

        self._referenced_files: set[str] = set()

    @property
    def slash_command_registry(self):
        return self._slash_command_registry

    @slash_command_registry.setter
    def slash_command_registry(self, value):
        self._slash_command_registry = value
        self._update_strategies()

    @property
    def file_searcher(self):
        return self._file_searcher

    @file_searcher.setter
    def file_searcher(self, value):
        self._file_searcher = value
        self._update_strategies()

    def _update_strategies(self):
        self.strategies = []
        if self._slash_command_registry:
            self.strategies.append(SlashCommandStrategy(self._slash_command_registry))
        if self._file_searcher:
            self.strategies.append(FileSearchStrategy(self._file_searcher))

    def get_referenced_files(self) -> set[str]:
        """Return the set of files that were selected via autocomplete and are still in the text."""
        current_text = self.text
        return {f for f in self._referenced_files if f"[📦{f}]" in current_text}

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

            self.app.action_submit_input()
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

        for strategy in self.strategies:
            context = strategy.check(self, row, col, line)
            if context:
                self._active_strategy = strategy
                self._active_context = context
                asyncio.create_task(self._fetch_suggestions(strategy, context))
                return

        self._hide_autocomplete()

    async def _fetch_suggestions(self, strategy: AutocompleteStrategy, context: CompletionContext):
        # Double check if we are still on the same context (async race condition)
        if self._active_strategy != strategy or self._active_context != context:
            return

        suggestions = await strategy.get_suggestions(context)

        # Verify again before displaying
        if self._active_strategy == strategy and self._active_context == context:
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
        self._active_strategy = None
        self._active_context = None
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

        if not self._active_strategy or not self._active_context:
            return

        selected = self._current_suggestions[self._selected_index]
        row, col = self.cursor_location

        self._active_strategy.apply_completion(self, selected, self._active_context, row, col)

        self._hide_autocomplete()

    def _update_autocomplete_display(self) -> None:
        """Update the autocomplete display in the popup."""
        try:
            popup = self.app.query_one("#autocomplete-popup", AutocompletePopup)
        except (NoMatches, AttributeError):
            popup = None

        if self._autocomplete_visible and self._current_suggestions and self._active_strategy:
            lines = [
                self._active_strategy.format_suggestion(item)
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

        try:
            hint_widget = self.app.query_one("#input-hint", Static)
            hint_widget.update("Enter to submit, Ctrl+Enter for newline")
        except (NoMatches, AttributeError):
            pass

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

    @property
    def slash_command_registry(self):
        return self._slash_command_registry

    @slash_command_registry.setter
    def slash_command_registry(self, value):
        self._slash_command_registry = value
        try:
            self.query_one("#user-input", SubmittableTextArea).slash_command_registry = value
        except NoMatches:
            pass

    @property
    def file_searcher(self):
        return self._file_searcher

    @file_searcher.setter
    def file_searcher(self, value):
        self._file_searcher = value
        try:
            self.query_one("#user-input", SubmittableTextArea).file_searcher = value
        except NoMatches:
            pass

    def on_mount(self) -> None:
        try:
            text_area = self.query_one("#user-input", SubmittableTextArea)
            if self._slash_command_registry:
                text_area.slash_command_registry = self._slash_command_registry
            if self._file_searcher:
                text_area.file_searcher = self._file_searcher
        except NoMatches:
            pass

    def compose(self) -> ComposeResult:
        yield Static("Enter to submit, Ctrl+Enter for newline", id="input-hint")
        yield SubmittableTextArea(id="user-input")
        yield AutocompletePopup(id="autocomplete-popup")

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
