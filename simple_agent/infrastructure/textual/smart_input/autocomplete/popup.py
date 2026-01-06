from dataclasses import dataclass
from typing import Optional, List, Callable
from textual.widgets import Static
from textual.message import Message
from textual.geometry import Offset, Size
from rich.text import Text

from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    CompletionResult,
    SuggestionList,
)


@dataclass(frozen=True)
class CompletionSeed:
    location: Offset
    text: str

    @property
    def width(self) -> int:
        return len(self.text)


@dataclass
class PopupLayout:
    width: int
    height: int
    offset: Offset
    lines: List[str]

    @classmethod
    def calculate(cls, suggestion_list: SuggestionList, seed: CompletionSeed, screen_size: Size) -> "PopupLayout":
        max_line_length = suggestion_list.max_content_width
        popup_width = min(max_line_length + 2, screen_size.width)
        available_width = max(1, popup_width - 2)

        trimmed_lines = suggestion_list.get_display_lines(available_width)
        popup_height = len(trimmed_lines)

        anchor_x = max(0, seed.location.x - seed.width)
        anchor_point = Offset(anchor_x, seed.location.y)

        offset = cls._calculate_placement(anchor_point, Size(popup_width, popup_height), screen_size)

        return cls(
            width=popup_width,
            height=popup_height,
            offset=offset,
            lines=trimmed_lines
        )

    @staticmethod
    def _calculate_placement(anchor_point: Offset, popup_size: Size, screen_size: Size) -> Offset:
        popup_height = popup_size.height
        popup_width = popup_size.width

        if popup_height < 1:
            popup_height = 1
        if popup_width < 1:
            popup_width = 1

        below_y = anchor_point.y + 1
        above_y = anchor_point.y - popup_height

        if below_y + popup_height <= screen_size.height:
            y = below_y
        elif above_y >= 0:
            y = above_y
        else:
            y = max(0, min(below_y, screen_size.height - popup_height))

        anchor_x = anchor_point.x - 1
        max_x = max(0, screen_size.width - popup_width)
        x = min(max(anchor_x, 0), max_x)

        return Offset(x, y)


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
        self._seed: Optional[CompletionSeed] = None

    def show(self, suggestion_list: SuggestionList, seed: CompletionSeed) -> None:
        if suggestion_list:
            self.suggestion_list = suggestion_list
            self._seed = seed
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

    def accept(self) -> None:
        selection = self.get_selection()
        if selection:
            self.close()
            self.post_message(self.Selected(selection))

    def get_action_for_key(self, key: str) -> Optional[Callable[[], None]]:
        if not self.display:
            return None

        if key == "down":
            return self.move_selection_down
        if key == "up":
            return self.move_selection_up
        if key in ("tab", "enter"):
            if self.get_selection():
                return self.accept
        if key == "escape":
            return self.close

        return None

    def _update_view(self) -> None:
        if not self.suggestion_list or not self.suggestion_list.suggestions:
            self.close()
            return

        if not self._seed:
            self.close()
            return

        self.display = True

        layout = PopupLayout.calculate(self.suggestion_list, self._seed, self.screen.size)

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
