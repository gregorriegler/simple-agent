from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import RichLog, Input, Footer


class TextualApp(App):

    CSS = """
    Screen {
        background: $surface;
    }

    #main-content {
        height: 1fr;
    }

    Horizontal {
        height: 100%;
    }

    #left-panel {
        width: 50%;
        height: 100%;
    }

    #right-panel {
        width: 50%;
        height: 100%;
    }

    RichLog {
        background: $surface;
        color: $text;
        border: solid $primary;
        height: 100%;
    }

    #tool-results {
        background: $surface;
        color: $text;
        border: solid $primary;
        height: 100%;
    }

    #user-input {
        height: 3;
        width: 100%;
        border: solid $primary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Horizontal(
                Container(
                    RichLog(highlight=True, markup=True, id="log"),
                    id="left-panel"
                ),
                Container(
                    RichLog(highlight=True, markup=True, id="tool-results"),
                    id="right-panel"
                ),
                id="main-content"
            ),
            Input(placeholder="Enter your message...", id="user-input")
        )
        yield Footer()

    def __init__(self, user_input=None):
        super().__init__()
        self.user_input = user_input

    def on_mount(self) -> None:
        self.query_one("#user-input", Input).focus()

    def on_unmount(self) -> None:
        if self.user_input:
            self.user_input.request_escape()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            if self.user_input:
                self.user_input.submit_input(event.value.strip())
            event.input.value = ""

    def write_message(self, message: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(message)

    def write_tool_result(self, message: str) -> None:
        tool_log = self.query_one("#tool-results", RichLog)
        tool_log.write(message)
