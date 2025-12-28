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

logger = logging.getLogger(__name__)


class SubmittableTextArea(TextArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slash_command_registry: SlashCommandRegistry | None = None
        self.file_searcher: FileSearcher | None = None
        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x = None
        self._active_trigger = None  # "/" or "@"
        self._trigger_word_start_index = None
        self._referenced_files: set[str] = set()
        self._autocomplete_popup: AutocompletePopup | None = None

    def set_autocomplete_popup(self, popup: AutocompletePopup) -> None:
        self._autocomplete_popup = popup

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
        # Get text up to cursor
        cursor_location = self.cursor_location
        # For simplicity, we only autocomplete on the last line where the cursor is
        # or properly handle multiline content.
        # TextArea.text is the whole text.

        # Get the line content and cursor column
        row, col = cursor_location
        try:
            line = self.document.get_line(row)
        except IndexError:
            self._hide_autocomplete()
            return

        # Check for slash command at start of text (simplest case)
        # Note: Slash commands are usually only at the very beginning of the prompt
        if row == 0 and col > 0 and line.startswith("/") and " " not in line[:col]:
            self._active_trigger = "/"
            self._trigger_word_start_index = 0
            self._show_autocomplete(line[:col])
            return

        # Check for file search (@)
        # We look for the word ending at cursor.
        # Find the start of the word before cursor
        text_before_cursor = line[:col]

        # Simple tokenization by space to find the current word being typed
        last_space_index = text_before_cursor.rfind(" ")
        word_start_index = last_space_index + 1
        current_word = text_before_cursor[word_start_index:]

        if current_word.startswith("@"):
            self._active_trigger = "@"
            self._trigger_word_start_index = word_start_index
            asyncio.create_task(self._show_file_autocomplete(current_word))
            return

        self._hide_autocomplete()

    def _show_autocomplete(self, text: str) -> None:
        """Show autocomplete suggestions for slash commands."""
        if not self.slash_command_registry:
            return

        # Extract the command part
        command = text
        suggestions = self.slash_command_registry.get_matching_commands(command)

        if suggestions:
            self._display_suggestions(suggestions)
        else:
            self._hide_autocomplete()

    async def _show_file_autocomplete(self, text: str) -> None:
        """Show autocomplete suggestions for files."""
        if not self.file_searcher:
            return

        # Remove '@' prefix for search
        query = text[1:]

        try:
            paths = await self.file_searcher.search(query)
            self._display_suggestions(paths, is_files=True)
        except Exception as e:
            logger.error(f"File search failed: {e}")
            self._hide_autocomplete()

    def _display_suggestions(self, suggestions: list, is_files: bool = False) -> None:
        was_visible = self._autocomplete_visible
        self._autocomplete_visible = True
        self._current_suggestions = suggestions
        self._selected_index = 0
        self._suggestions_are_files = is_files

        if not was_visible:
            self._autocomplete_anchor_x = self.cursor_screen_offset.x
            pass

        self._update_autocomplete_display()

    def _hide_autocomplete(self) -> None:
        """Hide autocomplete suggestions."""
        self._autocomplete_visible = False
        self._current_suggestions = []
        self._selected_index = 0
        self._autocomplete_anchor_x = None
        self._active_trigger = None
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

        selected = self._current_suggestions[self._selected_index]

        if self._active_trigger == "/":
            cmd_name = selected.name
            self.text = cmd_name + " "
            self.move_cursor_relative(columns=len(cmd_name) + 1)

        elif self._active_trigger == "@":
            row, col = self.cursor_location
            file_path = selected # selected is str
            self._referenced_files.add(file_path)

            start_col = self._trigger_word_start_index
            display_marker = f"[📦{file_path}]"

            self.replace(
                display_marker + " ",
                start=(row, start_col),
                end=(row, col),
                maintain_selection_offset=False,
            )

        self._hide_autocomplete()

    def _update_autocomplete_display(self) -> None:
        """Update the autocomplete display in the popup."""
        popup = self._autocomplete_popup

        if self._autocomplete_visible and self._current_suggestions:
            if self._suggestions_are_files:
                 lines = [
                    f"{path}"  # Just the path for files
                    for path in self._current_suggestions
                ]
            else:
                lines = [
                    f"{cmd.name} - {cmd.description}"
                    for cmd in self._current_suggestions
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
            popup = self.query_one("#autocomplete-popup", AutocompletePopup)
            text_area.set_autocomplete_popup(popup)

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
