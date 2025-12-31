import asyncio
from typing import List
from textual.widgets import Static
from rich.text import Text

from typing import Optional
from simple_agent.infrastructure.textual.autocomplete.autocompletion import SuggestionList, CompletionSearch, CompletionResult
from simple_agent.infrastructure.textual.autocomplete.geometry import PopupAnchor, PopupLayout

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.suggestion_list: Optional[SuggestionList] = None
        self._active: bool = False
        self._current_anchor: Optional[PopupAnchor] = None

    async def start(self, search: CompletionSearch, anchor: PopupAnchor) -> None:
        self._active = True
        self._current_anchor = anchor
        suggestions = await search.get_suggestions()
        if not self._active:
            return

        if suggestions:
            self.suggestion_list = SuggestionList(suggestions)
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
        self._active = False
        self.suggestion_list = None
        self.display = False

    def _update_view(self) -> None:
        """
        Render the suggestions list at the specified anchor.
        """
        if not self.suggestion_list or not self.suggestion_list.suggestions:
            self.close()
            return

        if not self._current_anchor:
            self.close()
            return

        self.display = True

        suggestions_text = [s.display_text for s in self.suggestion_list.suggestions]
        layout = PopupLayout.calculate(suggestions_text, self._current_anchor)

        # Update styles
        self.styles.width = layout.width
        self.styles.height = layout.height

        # Position
        self.absolute_offset = layout.offset

        # Render
        rendered = Text()
        for index, line in enumerate(layout.lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == self.suggestion_list.selected_index else ""
            rendered.append(line, style=style)

        super().update(rendered)
