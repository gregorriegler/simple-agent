from typing import Optional
from textual.widgets import Static
from rich.text import Text

from simple_agent.infrastructure.textual.autocomplete.geometry import (
    PopupLayout,
)

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
        self.popup_layout: Optional[PopupLayout] = None
        self._selected_index: int = 0

    def show(self, layout: PopupLayout, selected_index: int = 0) -> None:
        self.popup_layout = layout
        self._selected_index = selected_index
        self._update_view()

    def set_selected_index(self, index: int) -> None:
        self._selected_index = index
        self._update_view()

    def close(self) -> None:
        self.popup_layout = None
        self.display = False

    def _update_view(self) -> None:
        """
        Render the suggestions list at the specified layout.
        """
        if not self.popup_layout:
            self.close()
            return

        self.display = True

        # Update styles
        self.styles.width = self.popup_layout.width
        self.styles.height = self.popup_layout.height

        # Position
        self.absolute_offset = self.popup_layout.offset

        # Render
        rendered = Text()
        for index, line in enumerate(self.popup_layout.lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == self._selected_index else ""
            rendered.append(line, style=style)

        super().update(rendered)
