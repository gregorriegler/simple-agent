import asyncio
from dataclasses import dataclass
from typing import Any, Optional
from textual.widgets import Static
from textual.geometry import Offset, Size
from rich.text import Text

from simple_agent.infrastructure.textual.autocompletion import (
    CompletionResult,
    Suggestion,
    AutocompleteSession,
)

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
        """
        Initialize the AutocompletePopup.
        """
        super().__init__(**kwargs)
        self._session: Optional[AutocompleteSession] = None

    async def handle_key(self, key: str) -> bool | CompletionResult:
        if not self.display:
            return False

        if key in ("down", "up"):
            self._navigate(key)
            return True

        if key in ("tab", "enter"):
            return self._get_selection()

        if key == "escape":
            self.hide()
            return True

        return False

    def hide(self) -> None:
        self.display = False
        self._session = None

    def show(
        self,
        suggestions: list[Suggestion],
        anchor: PopupAnchor,
    ) -> None:
        self._session = AutocompleteSession(suggestions)
        self.display = True

        self._update_display(anchor)

    def _navigate(self, direction: str) -> None:
        if not self._session:
            return

        if direction == "down":
            self._session.move_down()
        elif direction == "up":
            self._session.move_up()

        self._render_content()

    def _get_selection(self) -> CompletionResult | None:
        if not self._session:
            return None

        result = self._session.get_selection()
        if result:
            self.hide()
        return result

    def _update_display(self, anchor: PopupAnchor) -> None:
        if not self._session or not self._session.suggestions:
            self.hide()
            return

        lines = [item.display_text for item in self._session.suggestions]

        max_line_length = max(len(line) for line in lines)
        popup_width = min(max_line_length + 2, anchor.max_width)
        available_width = max(1, popup_width - 2)
        trimmed_lines = [line[:available_width] for line in lines]
        popup_height = len(trimmed_lines)

        self.styles.width = popup_width
        self.styles.height = popup_height

        self.absolute_offset = anchor.get_placement(Size(popup_width, popup_height))

        self._render_content(trimmed_lines)

    def _render_content(self, lines: list[str] | None = None) -> None:
        if not self._session:
            return

        if lines is None:
            raw_lines = [item.display_text for item in self._session.suggestions]

            width = self.styles.width
            if width and hasattr(width, 'value'):
                 popup_width = int(width.value)
            else:
                 popup_width = 20

            available_width = max(1, popup_width - 2)
            lines = [line[:available_width] for line in raw_lines]

        rendered = Text()
        for index, line in enumerate(lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == self._session.selected_index else ""
            rendered.append(line, style=style)

        self.update(rendered)
