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
from simple_agent.infrastructure.textual.autocomplete.protocols import (
    AutocompleteRule,
)
from simple_agent.infrastructure.textual.autocomplete.domain import (
    CompletionResult,
    Cursor,
    CursorAndLine,
    MessageDraft,
    Suggestion,
    SuggestionList,
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

        self.rules = rules or []
        self.popup = AutocompletePopup()
        self.expander = FileContextExpander()

        self._referenced_files: set[str] = set()

    def on_mount(self) -> None:
        self.mount(self.popup)
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

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
        self._close_autocomplete()

    def _close_autocomplete(self) -> None:
        """Clear autocomplete state and hide popup."""
        self.popup.close()

    def on_autocomplete_popup_selected(self, message: AutocompletePopup.Selected) -> None:
        """Handle selection from the autocomplete popup."""
        self._apply_completion(message.result)
        message.stop()

    async def _on_key(self, event: events.Key) -> None:
        # Handle autocomplete navigation if active
        if self.popup.handle_key(event.key):
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

        self.call_after_refresh(self._trigger_autocomplete_check)

    def _trigger_autocomplete_check(self) -> None:
        """Helper to call popup check with current context."""
        cursor_and_line = self._get_cursor_and_line()
        if not cursor_and_line:
            self._close_autocomplete()
            return

        rule = self._find_triggered_rule(cursor_and_line)

        if rule:
            self._start_autocomplete(rule, cursor_and_line)
        else:
            self._close_autocomplete()

    def _get_cursor_and_line(self) -> Optional[CursorAndLine]:
        row, col = self.cursor_location
        try:
            line = self.document.get_line(row)
            return CursorAndLine(Cursor(row, col), line)
        except IndexError:
            return None

    def _find_triggered_rule(self, cursor_and_line: CursorAndLine) -> Optional[AutocompleteRule]:
        for rule in self.rules:
            if rule.trigger.is_triggered(cursor_and_line):
                return rule
        return None

    def _start_autocomplete(self, rule: AutocompleteRule, cursor_and_line: CursorAndLine) -> None:
        anchor = self._calculate_anchor(cursor_and_line)
        self.popup.load_suggestions(rule.provider, cursor_and_line, anchor)

    def _calculate_anchor(self, cursor_and_line: CursorAndLine) -> PopupAnchor:
        caret_location = CaretScreenLocation(
            offset=self.cursor_screen_offset,
            screen_size=self.app.screen.size
        )
        return caret_location.anchor_to_word(cursor_and_line)

    def _apply_completion(self, result: CompletionResult) -> None:
        row, col = self.cursor_location

        start_col = result.start_offset

        self.replace(
            result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        if result.attachments:
            self._referenced_files.update(result.attachments)
