from textual import events
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget

MIN_VERTICAL_PANEL_HEIGHT = 3


class Splitter(Widget):
    DEFAULT_CSS = """
    Splitter {
        width: 1;
        background: $surface-lighten-1;
    }

    Splitter:hover {
        background: $accent;
    }

    Splitter.horizontal {
        width: 100%;
        height: 1;
    }
    """

    can_focus = True
    dragging = reactive(False)

    def render(self) -> str:
        return ""

    def on_mouse_down(self, event: events.MouseDown) -> None:
        self.dragging = True
        self.capture_mouse()
        event.prevent_default()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self.dragging:
            self.dragging = False
            self.release_mouse()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self.dragging:
            parent = self.parent
            if isinstance(parent, ResizableHorizontal):
                parent.resize_panels(event.screen_x)
            elif isinstance(parent, ResizableVertical):
                parent.resize_panels(event.screen_y)


class ResizableHorizontal(Horizontal):
    def __init__(self, left_widget: Widget, right_widget: Widget, **kwargs):
        super().__init__(**kwargs)
        self.left_widget = left_widget
        self.right_widget = right_widget
        self.splitter = Splitter()

    def compose(self):
        yield self.left_widget
        yield self.splitter
        yield self.right_widget

    def resize_panels(self, x_position: int) -> None:
        container_width = self.size.width
        if container_width == 0:
            return

        left_width = max(20, min(container_width - 20, x_position - self.region.x))
        left_percent = (left_width / container_width) * 100
        right_percent = 100 - left_percent

        self.left_widget.styles.width = f"{left_percent}%"
        self.right_widget.styles.width = f"{right_percent}%"


class ResizableVertical(Vertical):
    def __init__(self, top_widget: Widget, bottom_widget: Widget, **kwargs):
        super().__init__(**kwargs)
        self.top_widget = top_widget
        self.bottom_widget = bottom_widget
        self.splitter = Splitter(classes="horizontal")
        # Default layout: top panel takes remaining space, todos use only their content height.
        self.top_widget.styles.height = "1fr"
        self.top_widget.styles.min_height = "0"
        self.bottom_widget.styles.height = "auto"
        self.bottom_widget.styles.min_height = "0"

    def compose(self):
        yield self.top_widget
        yield self.splitter
        yield self.bottom_widget

    def resize_panels(self, y_position: int) -> None:
        container_height = self.size.height
        if container_height == 0:
            return

        min_height = MIN_VERTICAL_PANEL_HEIGHT
        if container_height <= min_height * 2:
            top_height = container_height / 2
        else:
            top_height = max(
                min_height,
                min(container_height - min_height, y_position - self.region.y),
            )

        top_percent = (top_height / container_height) * 100
        bottom_percent = 100 - top_percent

        self.top_widget.styles.height = f"{top_percent}%"
        self.bottom_widget.styles.height = f"{bottom_percent}%"

    def set_bottom_visibility(self, visible: bool) -> None:
        display = "block" if visible else "none"
        self.bottom_widget.styles.display = display
        self.splitter.styles.display = display
