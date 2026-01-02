import asyncio
import logging
from typing import Optional, List
from dataclasses import dataclass

from rich.text import Text
from textual import events
from textual.message import Message
from textual.widgets import TextArea
from textual.geometry import Offset

from simple_agent.infrastructure.textual.autocomplete.popup import AutocompletePopup
from simple_agent.infrastructure.textual.autocomplete.geometry import (
    CaretScreenLocation,
    PopupAnchor,
)
from simple_agent.infrastructure.textual.autocomplete.rules import (
    AutocompleteRules,
)
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteRule,
)
from simple_agent.infrastructure.textual.autocomplete.domain import (
    Cursor,
    CursorAndLine,
    CompletionResult,
    Suggestion,
    SuggestionList,
    FileReferences,
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
        rules: List[AutocompleteRule] | None = None,
        id: str | None = None,
        **kwargs
    ):
        super().__init__(id=id, **kwargs)

        self.rules = AutocompleteRules(rules)
        self.popup = AutocompletePopup()
        self.expander = FileContextExpander()

        self._referenced_files = FileReferences()
        self._autocomplete_task: Optional[asyncio.Task] = None

    def on_mount(self) -> None:
        self.mount(self.popup)
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

    def get_referenced_files(self) -> set[str]:
        """Return the set of files that were selected via autocomplete and are still in the text."""
        return {ref.path for ref in self._referenced_files.filter_active_in(self.text)}

    def submit(self) -> None:
        """Submit the current text."""
        draft = CompletionResult(self.text, self._referenced_files)
        expanded_content = self.expander.expand(draft)

        self.post_message(self.Submitted(expanded_content))

        self.clear()
        self._referenced_files.clear()
        self._close_autocomplete()

    def _close_autocomplete(self) -> None:
        """Clear autocomplete state and hide popup."""
        if self._autocomplete_task:
            self._autocomplete_task.cancel()
            self._autocomplete_task = None
        self.popup.close()

    def on_autocomplete_popup_selected(self, message: AutocompletePopup.Selected) -> None:
        """Handle selection from the autocomplete popup."""
        self._apply_completion(message.result)
        message.stop()

    async def _on_key(self, event: events.Key) -> None:
        if self.popup.handle_key(event.key):
            self._consume_event(event)
            return

        if event.key == "enter":
            self._handle_enter(event)
            return

        if event.key in ("ctrl+enter", "ctrl+j"):
            self._handle_newline(event)
            return

        await super()._on_key(event)
        self.call_after_refresh(self._trigger_autocomplete_check)

    def _consume_event(self, event: events.Key) -> None:
        event.stop()
        event.prevent_default()

    def _handle_enter(self, event: events.Key) -> None:
        self.submit()
        self._consume_event(event)

    def _handle_newline(self, event: events.Key) -> None:
        self.insert("\n")
        self._consume_event(event)

    def _trigger_autocomplete_check(self) -> None:
        """Helper to call popup check with current context."""
        cursor_and_line = self._get_cursor_and_line()
        if not cursor_and_line:
            self._close_autocomplete()
            return

        if self._autocomplete_task:
            self._autocomplete_task.cancel()

        self._autocomplete_task = asyncio.create_task(self._run_autocomplete_check(cursor_and_line))

    async def _run_autocomplete_check(self, cursor_and_line: CursorAndLine) -> None:
        try:
            suggestion_list = await self.rules.suggest(cursor_and_line)
            if suggestion_list:
                anchor = self._calculate_anchor(cursor_and_line, suggestion_list)
                self.popup.show(suggestion_list, anchor)
            else:
                self.popup.close()
        except asyncio.CancelledError:
            pass
        finally:
            if self._autocomplete_task == asyncio.current_task():
                self._autocomplete_task = None

    def _get_cursor_and_line(self) -> Optional[CursorAndLine]:
        row, col = self.cursor_location
        try:
            line = self.document.get_line(row)
            return CursorAndLine(Cursor(row, col), line)
        except IndexError:
            return None

    def _calculate_anchor(self, cursor_and_line: CursorAndLine, suggestion_list: SuggestionList) -> PopupAnchor:
        caret_location = CaretScreenLocation(
            offset=self.cursor_screen_offset,
            screen_size=self.app.screen.size
        )
        return caret_location.anchor_to_column(
            suggestion_list.get_anchor_col(cursor_and_line),
            cursor_and_line.cursor.col
        )

    def _apply_completion(self, result: CompletionResult) -> None:
        row, col = self.cursor_location

        start_col = result.start_offset

        self.replace(
            result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        if result.files:
            self._referenced_files.add({ref.path for ref in result.files})
