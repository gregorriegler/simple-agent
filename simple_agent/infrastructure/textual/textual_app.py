import threading
import time
from pathlib import Path

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, Input, TabbedContent, TabPane, TextArea, Collapsible, Markdown

from simple_agent.application.tool_library import ToolResult
from simple_agent.infrastructure.textual.resizable_container import ResizableHorizontal


class TextualApp(App):
    @staticmethod
    def create_and_start(user_input=None):
        app = TextualApp(user_input)
        app._app_thread = threading.Thread(target=app.run, daemon=False)
        app._app_thread.start()
        time.sleep(0.5)
        return app

    def shutdown(self):
        if self.is_running:
            self.call_from_thread(self.exit)
        if self._app_thread and self._app_thread.is_alive():
            self._app_thread.join(timeout=2.0)
            if self._app_thread.is_alive():
                import sys
                print("Warning: TextualApp thread did not exit cleanly", file=sys.stderr)
    BINDINGS = [
        ("alt+left", "previous_tab", "Previous Tab"),
        ("alt+right", "next_tab", "Next Tab"),
        ("ctrl+c", "quit", "Quit"),
    ]

    CSS = """
    TabbedContent {
        height: 1fr;
    }

    #tab-content {
        height: 1fr;
    }

    ResizableHorizontal {
        height: 1fr;
    }

    #left-panel {
        width: 25%;
        padding: 1;
    }

    .left-panel-top {
        height: 1fr;
    }

    .left-panel-bottom {
        height: auto;
        max-height: 30;
        background: $surface-darken-1;
        border-top: solid $surface-lighten-1;
    }

    #right-panel {
        width: 75%;
        padding: 1;
    }

    .tool-call {
        color: $primary;
        text-style: bold;
    }

    .tool-result {
        color: $text-muted;
    }

    .tool-result-error {
        color: $error;
    }

    Pretty {
        border: round $primary;
        margin-bottom: 1;
    }

    #user-input {
        height: 3;
        border: solid $primary;
    }
    """

    def __init__(self, user_input=None):
        super().__init__()
        self.user_input = user_input
        self._app_thread = None
        self._pending_tool_calls: dict[str, str] = {}
        self._tool_result_collapsibles: dict[str, list[Collapsible]] = {}
        self._agent_panel_ids: dict[str, tuple[str, str]] = {}
        self._todo_widgets: dict[str, Markdown] = {}
        self._tool_results_to_agent: dict[str, str] = {}
        self._suppressed_tool_results: set[str] = set()

    def compose(self) -> ComposeResult:
        with Vertical():
            with TabbedContent(id="tabs"):
                with TabPane("Agent", id="agent-tab"):
                    yield self.create_agent_container("log", "tool-results", "Agent")
            yield Input(placeholder="Enter your message...", id="user-input", valid_empty=True)

    def create_agent_container(self, log_id, tool_results_id, agent_id):
        chat_scroll = VerticalScroll(Static("", id=log_id), id=f"{log_id}-scroll", classes="left-panel-top")
        todo = Markdown(self._load_todos(agent_id), id=f"{log_id}-todos")
        secondary_scroll = VerticalScroll(todo, id=f"{log_id}-secondary", classes="left-panel-bottom")
        left_panel = Vertical(chat_scroll, secondary_scroll, id="left-panel")
        right_panel = VerticalScroll(id=tool_results_id)
        self._tool_result_collapsibles[tool_results_id] = []
        self._agent_panel_ids[agent_id] = (log_id, tool_results_id)
        self._tool_results_to_agent[tool_results_id] = agent_id
        self._todo_widgets[agent_id] = todo
        self._pending_tool_calls.pop(tool_results_id, None)
        return ResizableHorizontal(left_panel, right_panel, id="tab-content")

    def on_mount(self) -> None:
        self.query_one("#user-input", Input).focus()

    def on_unmount(self) -> None:
        if self.user_input:
            self.user_input.close()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            if self.user_input:
                self.user_input.request_escape()
            event.prevent_default()
            return
        return

    def action_previous_tab(self) -> None:
        self._switch_tab(-1)

    def action_next_tab(self) -> None:
        self._switch_tab(1)

    def _switch_tab(self, direction: int) -> None:
        tabs = self.query_one("#tabs", TabbedContent)
        tab_panes = list(tabs.query(TabPane))
        if len(tab_panes) <= 1:
            return
        current_index = next((i for i, pane in enumerate(tab_panes) if pane.id == tabs.active), 0)
        new_index = (current_index + direction) % len(tab_panes)
        new_tab_id = tab_panes[new_index].id
        if new_tab_id:
            tabs.active = new_tab_id

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.user_input:
            self.user_input.submit_input(event.value.strip())
        event.input.value = ""

    def write_message(self, log_id: str, message: str) -> None:
        container = self.query_one(f"#{log_id}", Static)
        current = str(container.render())
        new_content = f"{current}\n{message}" if current else message
        container.update(new_content)
        self.query_one(f"#{log_id}-scroll", VerticalScroll).scroll_end(animate=False)

    def write_tool_call(self, tool_results_id: str, message: str) -> None:
        if "write-todos" in message:
            self._suppressed_tool_results.add(tool_results_id)
            self._pending_tool_calls.pop(tool_results_id, None)
            return
        self._pending_tool_calls[tool_results_id] = message

    def write_tool_result(self, tool_results_id: str, result: ToolResult) -> None:
        success = result.success
        if tool_results_id in self._suppressed_tool_results:
            self._suppressed_tool_results.discard(tool_results_id)
            self._pending_tool_calls.pop(tool_results_id, None)
            self._refresh_todos(tool_results_id)
            if success:
                return
        title_source = self._pending_tool_calls.pop(tool_results_id, None)
        message = result.display_body if result.display_body else result.message
        message = message or ""
        title_text = result.display_title if result.display_title else None
        if title_source is not None:
            lines = title_source.__str__().splitlines()
            default_title = lines[0] if lines else "Tool Result"
            other_lines = lines[1:]
            if title_text is None:
                title_text = default_title
            if success and other_lines and not result.display_body:
                message = "\n".join(other_lines)
        else:
            if title_text is None:
                title_text = "Tool Result"

        container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        collapsibles = self._tool_result_collapsibles.setdefault(tool_results_id, [])
        for collapsible in collapsibles:
            collapsible.collapsed = True

        classes = "tool-result" if success else "tool-result tool-result-error"
        language = result.display_language or "python"

        line_count = len(message.splitlines()) or 1
        height = min(line_count * 2 + 1, 30)
        text_area = TextArea(
            message,
            read_only=True,
            language=language,
            show_cursor=False,
            classes=classes,
        )
        text_area.styles.height = height
        text_area.styles.min_height = height

        collapsible = Collapsible(text_area, title=title_text, collapsed=False)
        collapsibles.append(collapsible)
        container.mount(collapsible)
        container.scroll_end(animate=False)
        self._refresh_todos(tool_results_id)

    def add_subagent_tab(self, agent_id: str, tab_title: str) -> tuple[str, str]:
        sanitized = agent_id.replace('/', '-')
        tab_id = f"tab-{sanitized}"
        log_id = f"log-{sanitized}"
        tool_results_id = f"tool-results-{sanitized}"

        new_tab = TabPane(tab_title, id=tab_id)
        new_tab.compose_add_child(self.create_agent_container(log_id, tool_results_id, agent_id))

        tabs = self.query_one("#tabs", TabbedContent)
        tabs.add_pane(new_tab)
        tabs.active = tab_id
        return log_id, tool_results_id

    def remove_subagent_tab(self, agent_id: str) -> None:
        tab_id = f"tab-{agent_id.replace('/', '-')}"
        self.query_one("#tabs", TabbedContent).remove_pane(tab_id)
        panel_ids = self._agent_panel_ids.pop(agent_id, None)
        if panel_ids:
            _, tool_results_id = panel_ids
            self._tool_result_collapsibles.pop(tool_results_id, None)
            self._pending_tool_calls.pop(tool_results_id, None)
            self._tool_results_to_agent.pop(tool_results_id, None)
            self._suppressed_tool_results.discard(tool_results_id)
        self._todo_widgets.pop(agent_id, None)

    def _load_todos(self, agent_id: str) -> str:
        sanitized = agent_id.replace("/", ".").replace("\\", ".")
        path = Path(f".{sanitized}.todos.md")
        if not path.exists():
            return ""
        content = path.read_text(encoding="utf-8").strip()
        return content if content else ""

    def _refresh_todos(self, tool_results_id: str) -> None:
        agent_id = self._tool_results_to_agent.get(tool_results_id)
        if not agent_id:
            return
        todo_widget = self._todo_widgets.get(agent_id)
        if not todo_widget:
            return
        todo_widget.update(self._load_todos(agent_id))
