from textual.app import App, ComposeResult
from textual.widgets import RichLog, Footer
from textual.containers import Container
from simple_agent.application.display import Display
from simple_agent.application.io import IO
from simple_agent.infrastructure.stdio import StdIO
import threading


class TextualDisplay(Display):

    def __init__(self, indent_level=0, agent_name="Agent", io: IO | None = None):
        self.indent_level = indent_level
        self.agent_name = agent_name
        self.io = io or StdIO()
        self.base_indent = "       " * (indent_level + 1)
        self.agent_prefix = "       " * indent_level + f"{agent_name}: "
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
                self.app.call_from_thread(self.app.write_message, f"{self.base_indent}{line}")

    def tool_result(self, result):
        self._ensure_app_running()
        lines = str(result).split('\n')
        first_three_lines = '\n'.join(lines[:3])
        if len(lines) > 3:
            first_three_lines += '\n... (truncated)'
        if self.app:
            for line in first_three_lines.split('\n'):
                self.app.call_from_thread(self.app.write_message, f"{self.base_indent}{line}")

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
        exit_msg = "       " * self.indent_level + "Exiting..."
        if self.app:
            self.app.call_from_thread(self.app.write_message, f"\n{exit_msg}")
            self.app.call_from_thread(self.app.exit)


class TextualApp(App):

    CSS = """
    Screen {
        background: $surface;
    }

    RichLog {
        background: $surface;
        color: $text;
        border: solid $primary;
    }
    """

    def compose(self) -> ComposeResult:
        yield Container(
            RichLog(highlight=True, markup=True, id="log"),
            Footer()
        )

    def write_message(self, message: str) -> None:
        log = self.query_one("#log", RichLog)
        log.write(message)
