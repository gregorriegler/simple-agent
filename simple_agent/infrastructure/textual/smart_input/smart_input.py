import asyncio
import logging
from typing import Optional, List

from textual import events
from textual.message import Message
from textual.widgets import TextArea

from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    Cursor,
    CursorAndLine,
    CompletionResult,
    FileReferences,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.popup import AutocompletePopup
from simple_agent.infrastructure.textual.smart_input.autocomplete.popup import (
    PopupAnchor,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    SuggestionProvider,
    CompositeSuggestionProvider,
)
from simple_agent.infrastructure.textual.widgets.file_loader import DiskFileLoader, XmlFormattingFileLoader

logger = logging.getLogger(__name__)

class SmartInput(TextArea):

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
        autocompletes: List[SuggestionProvider] | None = None,
        id: str | None = None,
        **kwargs
    ):
        super().__init__(id=id, **kwargs)

        self.autocompletes = CompositeSuggestionProvider(autocompletes)
        self.popup = AutocompletePopup()
        self.file_loader = XmlFormattingFileLoader(DiskFileLoader())

        self._referenced_files = FileReferences()
        self._autocomplete_task: Optional[asyncio.Task] = None

    def on_mount(self) -> None:
        self.mount(self.popup)
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

    def get_referenced_files(self) -> set[str]:
        return {ref.path for ref in self._referenced_files.filter_active_in(self.text)}

    def submit(self) -> None:
        result = CompletionResult(self.text, self._referenced_files)
        expanded_content = result.expand(self.file_loader)

        self.post_message(self.Submitted(expanded_content))

        self.clear()
        self._referenced_files.clear()
        self._close_autocomplete()

    def _close_autocomplete(self) -> None:
        if self._autocomplete_task:
            self._autocomplete_task.cancel()
            self._autocomplete_task = None
        self.popup.close()

    def on_autocomplete_popup_selected(self, message: AutocompletePopup.Selected) -> None:
        self._apply_completion(message.result)
        message.stop()

    async def _on_key(self, event: events.Key) -> None:
        if self.popup.display:
            if event.key == "down":
                self.popup.move_selection_down()
                self._consume_event(event)
                return
            elif event.key == "up":
                self.popup.move_selection_up()
                self._consume_event(event)
                return
            elif event.key in ("tab", "enter"):
                if self.popup.accept_selection():
                    self._consume_event(event)
                    return
            elif event.key == "escape":
                self.popup.close()
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
        cursor_and_line = self._get_cursor_and_line()
        if not cursor_and_line:
            self._close_autocomplete()
            return

        if self._autocomplete_task:
            self._autocomplete_task.cancel()

        self._autocomplete_task = asyncio.create_task(self._run_autocomplete_check(cursor_and_line))

    async def _run_autocomplete_check(self, cursor_and_line: CursorAndLine) -> None:
        try:
            suggestion_list = await self.autocompletes.suggest(cursor_and_line)
            if suggestion_list:
                # Calculate anchor
                anchor = PopupAnchor.create_at_column(
                    cursor_screen_offset=self.cursor_screen_offset,
                    screen_size=self.screen.size,
                    anchor_col=cursor_and_line.word_start_index,
                    current_col=self.cursor_location[1],
                )

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

    def _apply_completion(self, result: CompletionResult) -> None:
        row, col = self.cursor_location

        cursor_and_line = self._get_cursor_and_line()
        if cursor_and_line:
            start_col = cursor_and_line.word_start_index
        else:
            start_col = col

        self.replace(
            result.text,
            start=(row, start_col),
            end=(row, col),
            maintain_selection_offset=False,
        )

        if result.files:
            self._referenced_files.add({ref.path for ref in result.files})
