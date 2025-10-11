from textual.app import App, ComposeResult
from textual.widgets import RichLog, Footer, Static
from textual.containers import Container, Horizontal
from simple_agent.application.display import Display
from simple_agent.application.io import IO
from simple_agent.infrastructure.stdio import StdIO
import threading


class TextualDisplay(Display):

    def __init__(self, agent_name="Agent", io: IO | None = None):
        self.agent_name = agent_name
        self.io = io or StdIO()
        self.agent_prefix = f"{agent_name}: "
        self.app: TextualApp | None = None
        self.app_thread: threading.Thread | None = None

    def _ensure_app_running(self):
        if self.app is None:
            self.app = TextualApp()
            self.app_thread = threading.Thread(target=self._run_app, daemon=True)
            self.app_thread.start()
            import time
            time.sleep(0.5)

    def _run_app(self):
        if self.app:
            self.app.run()

    def assistant_says(self, message):
        self._ensure_app_running()
        lines = str(message).split('\n')
        if lines and self.app:
            self.app.call_from_thread(self.app.write_message, f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.app.call_from_thread(self.app.write_message, line)

    def tool_call(self, tool):
        self._ensure_app_running()
        lines = str(tool).split('\n')
        if self.app:
            self.app.call_from_thread(self.app.write_tool_result, lines)

    def tool_result(self, result):
        self._ensure_app_running()
        lines = str(result).split('\n')
        first_three_lines = '\n'.join(lines[:3])
        if len(lines) > 3:
            first_three_lines += '\n... (truncated)'
        if self.app:
            for line in first_three_lines.split('\n'):
                self.app.call_from_thread(self.app.write_tool_result, line)

    def continue_session(self):
        self._ensure_app_running()
        if self.app:
            self.app.call_from_thread(self.app.write_message, "Continuing session")

    def start_new_session(self):
        self._ensure_app_running()
        if self.app:
            self.app.call_from_thread(self.app.write_message, "Starting new session")

    def exit(self):
        self._ensure_app_running()
        if self.app:
            self.app.call_from_thread(self.app.write_message, "\nExiting...")
            self.app.call_from_thread(self.app.exit)


class TextualApp(App):

    CSS = """
    Screen {
        background: $surface;
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
    """

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Container(
                RichLog(highlight=True, markup=True, id="log"),
                id="left-panel"
            ),
            Container(
                RichLog(highlight=True, markup=True, id="tool-results"),
                id="right-panel"
            )
        )
        yield Footer()

    def write_message(self, message: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(message)

    def write_tool_result(self, message: str) -> None:
        tool_log = self.query_one("#tool-results", RichLog)
        tool_log.write(message)
