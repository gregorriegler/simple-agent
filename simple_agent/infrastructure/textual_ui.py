from queue import Queue
from threading import Event, Thread

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Static, TextLog

from simple_agent.application.display import Display
from simple_agent.application.user_input import UserInput


class _TextualSessionApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #body {
        height: 1fr;
        width: 1fr;
    }
    .panel {
        width: 1fr;
        height: 1fr;
    }
    TextLog {
        border: round $secondary;
    }
    #prompt {
        dock: bottom;
    }
    """

    def __init__(self, input_queue: Queue[str | None], ready_event: Event):
        super().__init__()
        self._input_queue = input_queue
        self._ready_event = ready_event
        self._chat_log: TextLog | None = None
        self._tool_log: TextLog | None = None

    def compose(self) -> ComposeResult:
        chat_panel = Vertical(Static("Chat"), TextLog(id="chat-log", wrap=True), id="chat", classes="panel")
        tool_panel = Vertical(Static("Tool Results"), TextLog(id="tool-log", wrap=True), id="tools", classes="panel")
        yield Horizontal(chat_panel, tool_panel, id="body")
        yield Input(placeholder="Press Enter to continue or type a message", id="prompt")

    def on_mount(self) -> None:
        self._chat_log = self.query_one("#chat-log", TextLog)
        self._tool_log = self.query_one("#tool-log", TextLog)
        prompt = self.query_one("#prompt", Input)
        prompt.focus()
        self._ready_event.set()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._input_queue.put(event.value.strip())
        event.input.value = ""

    def write_chat_lines(self, lines: list[str]) -> None:
        chat_log = self._require_chat_log()
        for line in lines:
            chat_log.write(line)
        chat_log.scroll_end(animate=False)

    def write_tool_lines(self, lines: list[str]) -> None:
        tool_log = self._require_tool_log()
        for line in lines:
            tool_log.write(line)
        tool_log.scroll_end(animate=False)

    def _require_chat_log(self) -> TextLog:
        if self._chat_log is None:
            raise RuntimeError("Chat log not ready")
        return self._chat_log

    def _require_tool_log(self) -> TextLog:
        if self._tool_log is None:
            raise RuntimeError("Tool log not ready")
        return self._tool_log


class TextualDisplay(Display):
    def __init__(self, app: _TextualSessionApp, input_queue: Queue[str | None], agent_name: str = "Agent"):
        self._app = app
        self._input_queue = input_queue
        self._agent_name = agent_name
        self._indent = "       "
        self._closed = False

    def assistant_says(self, message) -> None:
        lines = str(message).split("\n")
        if not lines:
            return
        first_line = f"{self._agent_name}: {lines[0]}" if lines[0] else f"{self._agent_name}:"
        remaining = [self._indent + line for line in lines[1:]]
        self._send_chat([first_line, *remaining])

    def tool_result(self, result) -> None:
        lines = str(result).split("\n")
        limited = lines[:3]
        if len(lines) > 3:
            limited.append("... (truncated)")
        formatted = [self._indent + line for line in limited]
        self._send_tool(formatted)

    def continue_session(self) -> None:
        self._send_chat(["Continuing session"])

    def start_new_session(self) -> None:
        self._send_chat(["Starting new session"])

    def exit(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._send_chat(["Exiting..."])
        self._input_queue.put(None)
        self._call(self._app.exit)

    def _send_chat(self, lines: list[str]) -> None:
        self._call(self._app.write_chat_lines, lines)

    def _send_tool(self, lines: list[str]) -> None:
        self._call(self._app.write_tool_lines, lines)

    def _call(self, target, *args) -> None:
        self._app.call_from_thread(target, *args)


class TextualUserInput(UserInput):
    def __init__(self, input_queue: Queue[str | None]):
        self._input_queue = input_queue

    def read(self) -> str:
        value = self._input_queue.get()
        if value is None:
            return ""
        return value

    def escape_requested(self) -> bool:
        return False


class TextualInterface:
    def __init__(self, agent_name: str = "Agent"):
        self._input_queue: Queue[str | None] = Queue()
        self._ready = Event()
        self._app = _TextualSessionApp(self._input_queue, self._ready)
        self.display = TextualDisplay(self._app, self._input_queue, agent_name)
        self.user_input = TextualUserInput(self._input_queue)
        self._thread = Thread(target=self._run_app, daemon=True)

    def start(self) -> None:
        self._thread.start()
        self._ready.wait()

    def stop(self) -> None:
        self.display.exit()
        self.wait_for_exit()

    def wait_for_exit(self) -> None:
        self._thread.join()

    def _run_app(self) -> None:
        self._app.run()
