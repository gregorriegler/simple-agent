import asyncio
import logging
from pathlib import Path

from rich.text import Text
from textual import events
from textual.css.query import NoMatches
from textual.geometry import Offset, Size
from textual.widgets import Static, TextArea

from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.file_search import FileSearcher

logger = logging.getLogger(__name__)

def calculate_autocomplete_position(
    cursor_offset: Offset,
    screen_size: Size,
    popup_height: int,
    popup_width: int,
) -> Offset:
    if popup_height < 1:
        popup_height = 1
    if popup_width < 1:
        popup_width = 1

    below_y = cursor_offset.y + 1
    above_y = cursor_offset.y - popup_height

    if below_y + popup_height <= screen_size.height:
        y = below_y
    elif above_y >= 0:
        y = above_y
    else:
        y = max(0, min(below_y, screen_size.height - popup_height))

    anchor_x = cursor_offset.x - 2
    max_x = max(0, screen_size.width - popup_width)
    x = min(max(anchor_x, 0), max_x)
    return Offset(x, y)


class AutocompletePopup(Static):
    DEFAULT_CSS = """
    AutocompletePopup {
        background: $surface;
        color: $text;
        padding: 0 1;
        overlay: screen;
        layer: overlay;
        display: none;
    }
    """

    def show_suggestions(
        self,
        lines: list[str],
        selected_index: int,
        cursor_offset: Offset,
        screen_size: Size,
    ) -> None:
        if not lines:
            self.hide()
            return

        max_line_length = max(len(line) for line in lines)
        popup_width = min(max_line_length + 2, screen_size.width)
        available_width = max(1, popup_width - 2)
        trimmed_lines = [line[:available_width] for line in lines]
        popup_height = len(trimmed_lines)

        self.styles.width = popup_width
        self.styles.height = popup_height
        self.absolute_offset = calculate_autocomplete_position(
            cursor_offset=cursor_offset,
            screen_size=screen_size,
            popup_height=popup_height,
            popup_width=popup_width,
        )

        rendered = Text()
        for index, line in enumerate(trimmed_lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == selected_index else ""
            rendered.append(line, style=style)

        self.update(rendered)
        self.display = True

    def hide(self) -> None:
        self.display = False


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

        # Avoid searching for empty string if desired, or allow it to show all files
        # showing all files might be too much, so maybe wait for 1 char?
        # let's allow it for now.

        try:
            paths = await self.file_searcher.search(query)
            # Wrap strings in simple objects to match structure expected by _display_suggestions if needed
            # or adapt _display_suggestions.
            # Slash commands are objects with .name and .description.
            # Let's make a simple wrapper or adapt the display logic.

            # Adapting display logic is better.
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
            # Calculate anchor X based on trigger word start
            # self.cursor_screen_offset is the absolute screen position of cursor
            # We want the popup to align with the start of the word.

            # Note: cursor_screen_offset calculation might be tricky with scrolling.
            # For now, let's try to approximate or just use cursor position.
            # Using cursor position matches the previous behavior for slash commands.
            # For @ files, it might be better to align with @.

            # Let's align with the cursor for now, simpler.
            self._autocomplete_anchor_x = self.cursor_screen_offset.x

            # Refinement: align with word start if possible.
            # This requires calculating the width of the text before cursor on this line.
            # Textual doesn't expose text measurement easily here without accessing internals.
            # We'll stick to cursor-aligned or left-aligned for now.
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
            # Slash command completion: replace the command
            # For slash commands, we assume it's at the start of the line (row 0)
            # We replace from 0 to cursor.

            # But wait, self.text is everything.
            # We need to be careful.

            # Simplification: Just replace the whole text if it's a slash command line
            # since slash commands are single-line prompts usually.

            cmd_name = selected.name
            self.text = cmd_name + " "
            self.move_cursor_relative(columns=len(cmd_name) + 1)

        elif self._active_trigger == "@":
            # File completion: replace the word under cursor
            # We know _trigger_word_start_index

            row, col = self.cursor_location
            file_path = selected # selected is str
            self._referenced_files.add(file_path)

            # Delete the current word (@...)
            # We are at `col`. The word started at `self._trigger_word_start_index`

            # Calculate length to delete
            # word length = col - self._trigger_word_start_index

            # Move cursor to start of word
            # But textual API for editing is: delete(start, end), insert(text, location)
            # Or use selection.

            # Easier approach with Textual TextArea:
            # Select the range then insert.

            start_col = self._trigger_word_start_index
            # We insert a visual marker [📦filename] for user feedback.
            display_marker = f"[📦{file_path}]"

            self.replace(
                display_marker + " ",
                start=(row, start_col),
                end=(row, col),
                maintain_selection_offset=False,
            )

            # Restore cursor is handled by replace somewhat, but let's ensure.
            # The replace puts cursor at the end of insertion usually.

        self._hide_autocomplete()

    def _update_autocomplete_display(self) -> None:
        """Update the autocomplete display in the popup."""
        try:
            popup = self.app.query_one("#autocomplete-popup", AutocompletePopup)
        except (NoMatches, AttributeError):
            popup = None

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
                # We try to position near cursor.
                # Use fixed anchor X if available to prevent popup from moving while typing.
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
