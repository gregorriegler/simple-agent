from textual import events
from textual.containers import Horizontal
from textual.widget import Widget
from textual.reactive import reactive


class Splitter(Widget):

    DEFAULT_CSS = """
    Splitter {
        width: 1;
        background: $surface-lighten-1;
    }

    Splitter:hover {
        background: $accent;
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
