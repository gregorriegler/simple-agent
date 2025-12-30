import asyncio
from dataclasses import dataclass
from typing import Any, Optional, List
from textual.widgets import Static
from textual.geometry import Offset, Size
from rich.text import Text

from simple_agent.infrastructure.textual.autocompletion import AutocompleteSession

@dataclass
class PopupAnchor:
    """Encapsulates the visual state needed to position the popup."""
    cursor_offset: Offset
    screen_size: Size

    def get_placement(self, popup_size: Size) -> Offset:
        """
        Calculate the best position for the popup given its size.
        """
        popup_height = popup_size.height
        popup_width = popup_size.width

        if popup_height < 1:
            popup_height = 1
        if popup_width < 1:
            popup_width = 1

        below_y = self.cursor_offset.y + 1
        above_y = self.cursor_offset.y - popup_height

        # Default to below if it fits, otherwise try above, else clamp
        if below_y + popup_height <= self.screen_size.height:
            y = below_y
        elif above_y >= 0:
            y = above_y
        else:
            y = max(0, min(below_y, self.screen_size.height - popup_height))

        # Horizontal positioning
        anchor_x = self.cursor_offset.x - 2
        max_x = max(0, self.screen_size.width - popup_width)
        x = min(max(anchor_x, 0), max_x)

        return Offset(x, y)

    @property
    def max_width(self) -> int:
        return self.screen_size.width

@dataclass
class CaretScreenLocation:
    offset: Offset
    screen_size: Size

    def anchor_to_word(self, cursor_and_line: Any) -> "PopupAnchor":
        """
        Creates a PopupAnchor positioned relative to the start of the current word.
        """
        word = cursor_and_line.current_word
        delta = cursor_and_line.col - word.start_index
        anchor_x = self.offset.x - delta

        # Ensure we don't go negative
        anchor_x = max(0, anchor_x)

        return PopupAnchor(
            cursor_offset=Offset(anchor_x, self.offset.y),
            screen_size=self.screen_size
        )

@dataclass
class PopupLayout:
    width: int
    height: int
    offset: Offset
    lines: List[str]

    @classmethod
    def calculate(cls, suggestions: List[str], anchor: PopupAnchor) -> "PopupLayout":
        max_line_length = max(len(line) for line in suggestions)
        popup_width = min(max_line_length + 2, anchor.max_width)
        available_width = max(1, popup_width - 2)
        trimmed_lines = [line[:available_width] for line in suggestions]
        popup_height = len(trimmed_lines)

        offset = anchor.get_placement(Size(popup_width, popup_height))

        return cls(
            width=popup_width,
            height=popup_height,
            offset=offset,
            lines=trimmed_lines
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

    def update_view(self, session: AutocompleteSession, anchor: PopupAnchor) -> None:
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
