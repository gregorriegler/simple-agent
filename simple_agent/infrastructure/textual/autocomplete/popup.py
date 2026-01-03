from typing import Optional
from textual.widgets import Static
from textual.message import Message
from rich.text import Text

from simple_agent.infrastructure.textual.autocomplete.domain import (
    CompletionResult,
    SuggestionList,
)
from simple_agent.infrastructure.textual.autocomplete.geometry import (
    PopupAnchor,
    PopupLayout,
)

class AutocompletePopup(Static):
    class Selected(Message):
        def __init__(self, result: CompletionResult):
            self.result = result
            super().__init__()

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.suggestion_list: Optional[SuggestionList] = None
        self._current_anchor: Optional[PopupAnchor] = None

    def show(self, suggestion_list: SuggestionList, anchor: PopupAnchor) -> None:
        if suggestion_list:
            self.suggestion_list = suggestion_list
            self._current_anchor = anchor
            self._update_view()
        else:
            self.close()

    def move_selection_down(self) -> None:
        if self.suggestion_list:
            self.suggestion_list.move_down()
            self._update_view()

    def move_selection_up(self) -> None:
        if self.suggestion_list:
            self.suggestion_list.move_up()
            self._update_view()

    def get_selection(self) -> Optional[CompletionResult]:
        if self.suggestion_list:
            return self.suggestion_list.get_selection()
        return None

    def close(self) -> None:
        self.suggestion_list = None
        self.display = False

    def accept_selection(self) -> bool:
        selection = self.get_selection()
        if selection:
            self.close()
            self.post_message(self.Selected(selection))
            return True
        return False

    def _update_view(self) -> None:
        if not self.suggestion_list or not self.suggestion_list.suggestions:
            self.close()
            return

        if not self._current_anchor:
            self.close()
            return

        self.display = True

        layout = PopupLayout.calculate(self.suggestion_list, self._current_anchor)

        self.styles.width = layout.width
        self.styles.height = layout.height

        self.absolute_offset = layout.offset

        rendered = Text()
        for index, line in enumerate(layout.lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == self.suggestion_list.selected_index else ""
            rendered.append(line, style=style)

        super().update(rendered)
