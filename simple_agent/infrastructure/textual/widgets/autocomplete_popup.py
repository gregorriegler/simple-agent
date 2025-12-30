import asyncio
from typing import List
from textual.widgets import Static
from rich.text import Text

from simple_agent.infrastructure.textual.autocompletion import SuggestionList
from simple_agent.infrastructure.textual.popup_geometry import PopupAnchor, PopupLayout

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

    def update_view(self, session: SuggestionList, anchor: PopupAnchor) -> None:
        """
        Render the suggestions list at the specified anchor.
        """
        if not session.suggestions:
            self.hide()
            return

        self.display = True

        suggestions_text = [s.display_text for s in session.suggestions]
        layout = PopupLayout.calculate(suggestions_text, anchor)

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
            style = "reverse" if index == session.selected_index else ""
            rendered.append(line, style=style)

        super().update(rendered)

    def hide(self) -> None:
        self.display = False
