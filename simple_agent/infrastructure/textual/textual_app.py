import os
import signal
import threading
import time
from pathlib import Path

from rich.syntax import Syntax
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, Input, TabbedContent, TabPane, TextArea, Collapsible, Markdown

from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_library import ToolResult
from simple_agent.infrastructure.textual.textual_messages import (
    AddSubagentTabMessage,
    AssistantSaysMessage,
    RefreshTodosMessage,
    RemoveAgentTabMessage,
    SessionStatusMessage,
    ToolCallMessage,
    ToolResultMessage,
    UserSaysMessage,
)
from simple_agent.infrastructure.textual.resizable_container import ResizableHorizontal, ResizableVertical


class TextualApp(App):
    @staticmethod
    def create_and_start(user_input=None, root_agent_id: AgentId = AgentId("Agent")):
        app = TextualApp(user_input, root_agent_id)
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
        ("ctrl+q", "quit", "Quit"),
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

    .left-panel-top,
    .left-panel-bottom {
        min-height: 0;
    }

    .left-panel-bottom {
        background: $surface-darken-1;
        overflow-y: auto;
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
        background: $surface;
    }

    .tool-result-error {
        border: round $error;
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

    def __init__(self, user_input=None, root_agent_id: AgentId = AgentId("Agent")):
        super().__init__()
        self.user_input = user_input
        self._root_agent_id = root_agent_id
        self._app_thread = None
        self._pending_tool_calls: dict[str, dict[str, tuple[str, TextArea, Collapsible]]] = {}
        self._tool_result_collapsibles: dict[str, list[Collapsible]] = {}
        self._agent_panel_ids: dict[AgentId, tuple[str, str]] = {}
        self._todo_widgets: dict[str, Markdown] = {}
        self._tool_results_to_agent: dict[str, AgentId] = {}
        self._suppressed_tool_calls: set[str] = set()
        self._signal_on_unmount = False

    def has_agent_tab(self, agent_id: AgentId) -> bool:
        return agent_id in self._agent_panel_ids

    @staticmethod
    def panel_ids_for(agent_id: AgentId) -> tuple[str, str, str]:
        sanitized = agent_id.for_ui()
        tab_id = f"tab-{sanitized}"
        log_id = f"log-{sanitized}"
        tool_results_id = f"tool-results-{sanitized}"
        return tab_id, log_id, tool_results_id

    def compose(self) -> ComposeResult:
        tab_id, log_id, tool_results_id = self.panel_ids_for(self._root_agent_id)
        with Vertical():
            with TabbedContent(id="tabs"):
                with TabPane(self._root_agent_id.raw, id=tab_id):
                    yield self.create_agent_container(log_id, tool_results_id, self._root_agent_id)
            yield Input(placeholder="Enter your message...", id="user-input", valid_empty=True)

    def create_agent_container(self, log_id, tool_results_id, agent_id):
        chat_scroll = VerticalScroll(Static("", id=log_id), id=f"{log_id}-scroll", classes="left-panel-top")
        todo = Markdown(self._load_todos(agent_id), id=f"{log_id}-todos")
        secondary_scroll = VerticalScroll(todo, id=f"{log_id}-secondary", classes="left-panel-bottom")
        left_panel = ResizableVertical(chat_scroll, secondary_scroll, id="left-panel")
        right_panel = VerticalScroll(id=tool_results_id)
        self._tool_result_collapsibles[tool_results_id] = []
        self._agent_panel_ids[agent_id] = (log_id, tool_results_id)
        self._tool_results_to_agent[tool_results_id] = agent_id
        self._todo_widgets[str(agent_id)] = todo
        self._pending_tool_calls[tool_results_id] = {}
        return ResizableHorizontal(left_panel, right_panel, id="tab-content")

    def on_mount(self) -> None:
        self.query_one("#user-input", Input).focus()

    def on_unmount(self) -> None:
        if self.user_input:
            self.user_input.close()
        if self._signal_on_unmount:
            def _raise_sigint() -> None:
                try:
                    time.sleep(0.05)
                    os.kill(os.getpid(), signal.SIGINT)
                except BaseException:
                    pass

            threading.Thread(target=_raise_sigint, daemon=True).start()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            if self.user_input:
                self.user_input.request_escape()
            event.prevent_default()
            return
        return

    def action_quit(self) -> None:
        """Ensure Ctrl+C / Ctrl+Q stop the agent, not just the UI."""
        if self.user_input:
            self.user_input.close()
        self._signal_on_unmount = True
        self.exit()

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

    def write_tool_call(self, tool_results_id: str, call_id: str, message: str) -> None:
        pending_for_panel = self._pending_tool_calls.setdefault(tool_results_id, {})
        if "write-todos" in message:
            pending_for_panel.pop(call_id, None)
            self._suppressed_tool_calls.add(call_id)
            return
        container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        collapsibles = self._tool_result_collapsibles.setdefault(tool_results_id, [])
        for collapsible in collapsibles:
            collapsible.collapsed = True

        text_area = TextArea(
            "In Progress ...",
            read_only=True,
            language="markdown",
            show_cursor=False,
            classes="tool-call",
        )
        text_area.styles.height = 3
        text_area.styles.min_height = 3

        lines = message.splitlines()
        default_title = lines[0] if lines else "Tool Call"
        collapsible = Collapsible(text_area, title=default_title, collapsed=False)
        collapsibles.append(collapsible)
        container.mount(collapsible)
        container.scroll_end(animate=False)

        pending_for_panel[call_id] = (message, text_area, collapsible)

    def write_tool_result(self, tool_results_id: str, call_id: str, result: ToolResult) -> None:
        pending_for_panel = self._pending_tool_calls.setdefault(tool_results_id, {})
        success = result.success
        if call_id in self._suppressed_tool_calls:
            self._suppressed_tool_calls.discard(call_id)
            pending_for_panel.pop(call_id, None)
            self._refresh_todos(tool_results_id)
            return
        title_source, text_area, call_collapsible = pending_for_panel.pop(call_id)
        message = result.display_body if result.display_body else result.message
        message = message or ""
        title_text = result.display_title if result.display_title else None
        lines = title_source.splitlines()
        default_title = lines[0] if lines else "Tool Result"
        other_lines = lines[1:]
        if title_text is None:
            title_text = default_title
        if success and other_lines and not result.display_body and not message.strip():
            message = "\n".join(other_lines)

        collapsibles = self._tool_result_collapsibles.setdefault(tool_results_id, [])
        for existing in collapsibles:
            existing.collapsed = True
        call_collapsible.collapsed = False

        classes = "tool-result" if success else "tool-result tool-result-error"
        language = result.display_language or "python"

        if language == "diff":
            diff_renderable = Syntax(
                message,
                "diff",
                theme="ansi_dark",
                line_numbers=False,
                word_wrap=True,
            )
            diff_widget = Static(diff_renderable)
            for cls in classes.split():
                diff_widget.add_class(cls)
            height = min((len(message.splitlines()) or 1) * 2 + 1, 30)
            diff_widget.styles.height = height
            diff_widget.styles.min_height = height
            text_area.remove()
            contents = call_collapsible.query_one(Collapsible.Contents)
            contents.mount(diff_widget)
        else:
            line_count = len(message.splitlines()) or 1
            height = min(line_count * 2 + 1, 30)
            text_area.load_text(message)
            text_area.language = language
            text_area.remove_class("tool-call")
            for cls in ("tool-result", "tool-result-error"):
                text_area.remove_class(cls)
            for cls in classes.split():
                text_area.add_class(cls)
            text_area.styles.height = height
            text_area.styles.min_height = height

        call_collapsible.title = title_text
        container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        container.scroll_end(animate=False)
        self._refresh_todos(tool_results_id)

    def add_subagent_tab(self, agent_id: AgentId, tab_title: str) -> tuple[str, str]:
        tab_id, log_id, tool_results_id = self.panel_ids_for(agent_id)

        new_tab = TabPane(tab_title, id=tab_id)
        new_tab.compose_add_child(self.create_agent_container(log_id, tool_results_id, agent_id))

        tabs = self.query_one("#tabs", TabbedContent)
        tabs.add_pane(new_tab)
        tabs.active = tab_id
        return log_id, tool_results_id

    def remove_subagent_tab(self, agent_id: AgentId) -> None:
        tab_id, _, tool_results_id = self.panel_ids_for(agent_id)
        self.query_one("#tabs", TabbedContent).remove_pane(tab_id)
        panel_ids = self._agent_panel_ids.pop(agent_id, None)
        if panel_ids:
            self._tool_result_collapsibles.pop(tool_results_id, None)
            self._pending_tool_calls.pop(tool_results_id, None)
            self._tool_results_to_agent.pop(tool_results_id, None)
            prefix = f"{agent_id}::tool_call::"
            self._suppressed_tool_calls = {
                call_id for call_id in self._suppressed_tool_calls if not call_id.startswith(prefix)
            }
        self._todo_widgets.pop(str(agent_id), None)

    def _load_todos(self, agent_id: AgentId) -> str:
        path = Path(agent_id.todo_filename())
        if not path.exists():
            return ""
        content = path.read_text(encoding="utf-8").strip()
        return content if content else ""

    def _refresh_todos(self, tool_results_id: str) -> None:
        agent_id = self._tool_results_to_agent.get(tool_results_id)
        if not agent_id:
            return
        self._refresh_todos_for_agent(agent_id)

    def _refresh_todos_for_agent(self, agent_id: AgentId) -> None:
        todo_widget = self._todo_widgets.get(str(agent_id))
        if not todo_widget:
            return
        todo_widget.update(self._load_todos(agent_id))

    def on_user_says_message(self, message: UserSaysMessage) -> None:
        self.write_message(message.log_id, message.content)

    def on_assistant_says_message(self, message: AssistantSaysMessage) -> None:
        self.write_message(message.log_id, message.content)

    def on_tool_call_message(self, message: ToolCallMessage) -> None:
        self.write_tool_call(message.tool_results_id, message.call_id, message.tool_str)

    def on_tool_result_message(self, message: ToolResultMessage) -> None:
        self.write_tool_result(message.tool_results_id, message.call_id, message.result)

    def on_session_status_message(self, message: SessionStatusMessage) -> None:
        self.write_message(message.log_id, message.status)

    def on_add_subagent_tab_message(self, message: AddSubagentTabMessage) -> None:
        self.add_subagent_tab(message.agent_id, message.tab_title)

    def on_remove_agent_tab_message(self, message: RemoveAgentTabMessage) -> None:
        self.remove_subagent_tab(message.agent_id)

    def on_refresh_todos_message(self, message: RefreshTodosMessage) -> None:
        self._refresh_todos_for_agent(message.agent_id)
