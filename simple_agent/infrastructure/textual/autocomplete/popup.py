import asyncio
from typing import List, Optional
from textual.widgets import Static
from textual.message import Message
from rich.text import Text

from simple_agent.infrastructure.textual.autocomplete import SuggestionList, CompletionResult, Suggestion
from simple_agent.infrastructure.textual.autocomplete.geometry import PopupAnchor, PopupLayout

class AutocompletePopup(Static):
    class Selected(Message):
        """Posted when a suggestion is selected."""
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

    def show_suggestions(self, suggestions: List[Suggestion], anchor: PopupAnchor) -> None:
        self._current_anchor = anchor

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
        self.suggestion_list = None
        self.display = False

    def handle_key(self, key: str) -> bool:
        """
        Handle keyboard interaction for the popup.

        Returns:
            bool: True if the key was handled (consumed), False otherwise.
        """
        if not self.display or not self.suggestion_list:
            return False

        if key == "down":
            self.move_selection_down()
            return True
        elif key == "up":
            self.move_selection_up()
            return True
        elif key in ("tab", "enter"):
            selection = self.get_selection()
            if selection:
                self.close()
                self.post_message(self.Selected(selection))
                return True
            # If no selection is possible (shouldn't happen if active has items),
            # we generally don't consume enter unless we want to block submission?
            # Existing logic suggests we only consume if result is found.
            return False
        elif key == "escape":
            self.close()
            return True

        return False

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

        layout = PopupLayout.calculate(self.suggestion_list, self._current_anchor)

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
