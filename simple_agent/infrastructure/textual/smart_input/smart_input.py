import asyncio
import logging

from textual import events
from textual.message import Message
from textual.widgets import TextArea

from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    CompletionResult,
    Cursor,
    CursorAndLine,
    SuggestionProvider,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.popup import (
    AutocompletePopup,
    CompletionSeed,
)

logger = logging.getLogger(__name__)


class SmartInput(TextArea):
    class Submitted(Message):
        def __init__(self, result: CompletionResult, source: "SmartInput"):
            self.result = result
            self._source = source
            super().__init__()

        @property
        def control(self) -> "SmartInput":
            return self._source

    DEFAULT_CSS = """
    SmartInput {
        height: auto;
        dock: bottom;
        border: solid $primary;
    }
    """

    def __init__(self, provider: SuggestionProvider, id: str | None = None, **kwargs):
        super().__init__(id=id, **kwargs)

        self.provider = provider
        self.popup = AutocompletePopup(target_widget=self)

        self._autocomplete_task: asyncio.Task | None = None

    def on_mount(self) -> None:
        self.app.mount(self.popup)
        self.border_subtitle = "Enter to submit, Ctrl+Enter for newline"

    def submit(self) -> None:
        result = CompletionResult(self.text)

        self.post_message(self.Submitted(result, self))

        self.clear()
        self._close_autocomplete()

    def _close_autocomplete(self) -> None:
        if self._autocomplete_task:
            self._autocomplete_task.cancel()
            self._autocomplete_task = None
        self.popup.close()

    def on_autocomplete_popup_selected(
        self, message: AutocompletePopup.Selected
    ) -> None:
        self._apply_completion(message.result)
        message.stop()

    async def _on_key(self, event: events.Key) -> None:
        action = self.popup.get_action_for_key(event.key)
        if action:
            action()
            self._consume_event(event)
            return

        if event.key == "enter":
            self._handle_enter(event)
            return

        if event.key in ("ctrl+enter", "ctrl+j", "shift+enter"):
            self._handle_newline(event)
            return

        await super()._on_key(event)

    def on_text_area_changed(self) -> None:
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

        self._autocomplete_task = asyncio.create_task(
            self._run_autocomplete_check(cursor_and_line)
        )

    async def _run_autocomplete_check(self, cursor_and_line: CursorAndLine) -> None:
        try:
            suggestion_list = await self.provider.suggest(cursor_and_line)
            if suggestion_list:
                seed = CompletionSeed(
                    location=self.cursor_screen_offset, text=cursor_and_line.word
                )
                self.popup.show(suggestion_list, seed)
            else:
                self.popup.close()
        except asyncio.CancelledError:
            pass
        finally:
            if self._autocomplete_task == asyncio.current_task():
                self._autocomplete_task = None

    def _get_cursor_and_line(self) -> CursorAndLine | None:
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
