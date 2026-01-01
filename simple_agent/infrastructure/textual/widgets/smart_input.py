import asyncio
import logging
from typing import Optional, List

from textual import events
from textual.message import Message
from textual.widgets import TextArea

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
        self.popup = AutocompletePopup(id="autocomplete-popup")
        self.expander = FileContextExpander()
        self._current_autocomplete_token: object | None = None

        self._referenced_files: set[str] = set()

    def on_mount(self) -> None:
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"
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
        self._close_autocomplete()

    def _close_autocomplete(self) -> None:
        """Clear autocomplete state and hide popup."""
        self.popup.close()
        self._current_autocomplete_token = None

    async def _on_key(self, event: events.Key) -> None:
        # Handle autocomplete navigation if active
        if self._handle_autocomplete_key(event):
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

    def _handle_autocomplete_key(self, event: events.Key) -> bool:
        """
        Handles key events related to autocomplete navigation.
        Returns True if the event was handled and propagation should stop.
        """
        if not self.popup.display or not self.popup.suggestion_list:
            return False

        if event.key == "down":
            self.popup.move_selection_down()
            event.stop()
            event.prevent_default()
            return True
        elif event.key == "up":
            self.popup.move_selection_up()
            event.stop()
            event.prevent_default()
            return True
        elif event.key in ("tab", "enter"):
            result = self.popup.get_selection()
            if result:
                self._apply_completion(result)
                self._close_autocomplete()
                event.stop()
                event.prevent_default()
                return True
        elif event.key == "escape":
            self._close_autocomplete()
            event.stop()
            event.prevent_default()
            return True

        return False

    def _trigger_autocomplete_check(self) -> None:
        """Helper to call popup check with current context."""
        row, col = self.cursor_location
        try:
            line = self.document.get_line(row)
        except IndexError:
            self._close_autocomplete()
            return

        cursor_and_line = CursorAndLine(Cursor(row, col), line)

        for rule in self.rules:
            if rule.trigger.is_triggered(cursor_and_line):
                self._start_autocomplete(rule, cursor_and_line)
                return

        self._close_autocomplete()

    def _start_autocomplete(self, rule: AutocompleteRule, cursor_and_line: CursorAndLine) -> None:
        # Create Anchor
        caret_location = CaretScreenLocation(
            offset=self.cursor_screen_offset,
            screen_size=self.app.screen.size
        )
        anchor = caret_location.anchor_to_word(cursor_and_line)

        # Start a new session token
        token = object()
        self._current_autocomplete_token = token

        asyncio.create_task(self._fetch_and_show_suggestions(rule, cursor_and_line, anchor, token))

    async def _fetch_and_show_suggestions(
        self,
        rule: AutocompleteRule,
        cursor_and_line: CursorAndLine,
        anchor: PopupAnchor,
        token: object
    ) -> None:
        suggestions = await rule.provider.fetch(cursor_and_line)

        # Check if this fetch is still relevant
        if self._current_autocomplete_token is not token:
            return

        self.popup.show_suggestions(suggestions, anchor)

    def _apply_completion(self, result: CompletionResult) -> None:
        row, col = self.cursor_location

        # Simplified: no None check needed
        start_col = result.start_offset

        self.replace(
            result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        if result.attachments:
            self._referenced_files.update(result.attachments)
