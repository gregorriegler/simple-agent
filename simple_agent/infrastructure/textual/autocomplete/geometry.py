from dataclasses import dataclass
from typing import List

from textual.geometry import Offset, Size

from simple_agent.infrastructure.textual.autocomplete.domain import SuggestionList


@dataclass
class PopupAnchor:
    cursor_offset: Offset
    screen_size: Size

    @classmethod
    def create_at_column(
        cls,
        cursor_screen_offset: Offset,
        screen_size: Size,
        anchor_col: int,
        current_col: int,
    ) -> "PopupAnchor":
        delta = current_col - anchor_col
        anchor_x = max(0, cursor_screen_offset.x - delta)

        return cls(
            cursor_offset=Offset(anchor_x, cursor_screen_offset.y),
            screen_size=screen_size,
        )

    def get_placement(self, popup_size: Size) -> Offset:
        popup_height = popup_size.height
        popup_width = popup_size.width

        if popup_height < 1:
            popup_height = 1
        if popup_width < 1:
            popup_width = 1

        below_y = self.cursor_offset.y + 1
        above_y = self.cursor_offset.y - popup_height

        if below_y + popup_height <= self.screen_size.height:
            y = below_y
        elif above_y >= 0:
            y = above_y
        else:
            y = max(0, min(below_y, self.screen_size.height - popup_height))

        anchor_x = self.cursor_offset.x - 2
        max_x = max(0, self.screen_size.width - popup_width)
        x = min(max(anchor_x, 0), max_x)

        return Offset(x, y)

    @property
    def max_width(self) -> int:
        return self.screen_size.width


@dataclass
class PopupLayout:
    width: int
    height: int
    offset: Offset
    lines: List[str]

    @classmethod
    def calculate(cls, suggestion_list: SuggestionList, anchor: PopupAnchor) -> "PopupLayout":
        max_line_length = suggestion_list.max_content_width
        popup_width = min(max_line_length + 2, anchor.max_width)
        available_width = max(1, popup_width - 2)

        trimmed_lines = suggestion_list.get_display_lines(available_width)
        popup_height = len(trimmed_lines)

        offset = anchor.get_placement(Size(popup_width, popup_height))

        return cls(
            width=popup_width,
            height=popup_height,
            offset=offset,
            lines=trimmed_lines
        )
