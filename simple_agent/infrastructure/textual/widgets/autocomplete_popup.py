from textual.widgets import Static
from textual.geometry import Offset, Size
from rich.text import Text

def calculate_autocomplete_position(
    cursor_offset: Offset,
    screen_size: Size,
    popup_height: int,
    popup_width: int,
) -> Offset:
    if popup_height < 1:
        popup_height = 1
    if popup_width < 1:
        popup_width = 1

    below_y = cursor_offset.y + 1
    above_y = cursor_offset.y - popup_height

    if below_y + popup_height <= screen_size.height:
        y = below_y
    elif above_y >= 0:
        y = above_y
    else:
        y = max(0, min(below_y, screen_size.height - popup_height))

    anchor_x = cursor_offset.x - 2
    max_x = max(0, screen_size.width - popup_width)
    x = min(max(anchor_x, 0), max_x)
    return Offset(x, y)


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

    def show_suggestions(
        self,
        lines: list[str],
        selected_index: int,
        cursor_offset: Offset,
        screen_size: Size,
    ) -> None:
        if not lines:
            self.hide()
            return

        max_line_length = max(len(line) for line in lines)
        popup_width = min(max_line_length + 2, screen_size.width)
        available_width = max(1, popup_width - 2)
        trimmed_lines = [line[:available_width] for line in lines]
        popup_height = len(trimmed_lines)

        self.styles.width = popup_width
        self.styles.height = popup_height
        self.absolute_offset = calculate_autocomplete_position(
            cursor_offset=cursor_offset,
            screen_size=screen_size,
            popup_height=popup_height,
            popup_width=popup_width,
        )

        rendered = Text()
        for index, line in enumerate(trimmed_lines):
            if index:
                rendered.append("\n")
            style = "reverse" if index == selected_index else ""
            rendered.append(line, style=style)

        self.update(rendered)
        self.display = True

    def hide(self) -> None:
        self.display = False
