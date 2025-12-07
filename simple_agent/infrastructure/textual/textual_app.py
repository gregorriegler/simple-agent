import logging
import os
import signal
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

from rich.syntax import Syntax
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.css.query import NoMatches
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
    UpdateTabTitleMessage,
    UserSaysMessage,
)
from simple_agent.infrastructure.textual.resizable_container import ResizableHorizontal, ResizableVertical


class SubmittableTextArea(TextArea):

    def _on_key(self, event: events.Key) -> None:
        # ctrl+j is how Windows/mintty sends Ctrl+Enter
        if event.key in ("ctrl+enter", "ctrl+j"):
            self.app.action_submit_input()
            event.stop()
            event.prevent_default()
            return
        super()._on_key(event)


class TextualApp(App):
    @staticmethod
    def create_and_start(user_input=None, root_agent_id: AgentId = AgentId("Agent")):
        app = TextualApp(user_input, root_agent_id)

        def run_with_suppressed_shutdown_error():
            try:
                app.run()
            except RuntimeError as e:
                # Suppress "cannot schedule new futures after shutdown" which occurs
                # when asyncio.run() cleans up the executor before Textual finishes
                # stopping its timers. This is benign during app exit.
                if "cannot schedule new futures after shutdown" not in str(e):
                    raise

        app._app_thread = threading.Thread(target=run_with_suppressed_shutdown_error, daemon=False)
        app._app_thread.start()
        time.sleep(0.5)
        return app

    @staticmethod
    def create_and_start_test(user_input=None, root_agent_id: AgentId = AgentId("Agent")):
        """Start the app in test mode using Textual's run_test() for headless testing."""
        import asyncio
        import io
        import sys

        app = TextualApp(user_input, root_agent_id)
        app._test_ready = threading.Event()
        app._test_shutdown = threading.Event()

        async def run_test_wrapper():
            async with app.run_test() as pilot:
                # On Windows, Textual's headless mode tries to write to _original_stdout/_original_stderr
                # which may have invalid handles. Replace them with valid streams.
                if sys.platform == "win32":
                    app._original_stdout = io.StringIO()
                    app._original_stderr = io.StringIO()
                app._pilot = pilot
                await pilot.pause()  # Wait for app to fully mount
                app._test_ready.set()
                while not app._test_shutdown.is_set():
                    await asyncio.sleep(0.1)

        def thread_target():
            asyncio.run(run_test_wrapper())

        app._app_thread = threading.Thread(target=thread_target, daemon=False)
        app._app_thread.start()
        app._test_ready.wait()
        return app

    def shutdown(self):
        if hasattr(self, '_test_shutdown'):
            self._test_shutdown.set()
            if self._app_thread and self._app_thread.is_alive():
                self._app_thread.join(timeout=2.0)
        elif self.is_running:
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
        ("ctrl+enter", "submit_input", "Submit"),
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
        padding: 1 1 0 1;
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
        height: 5;
        min-height: 3;
        max-height: 10;
        border: solid $primary;
    }

    #input-hint {
        height: 1;
        color: $text-muted;
        text-align: right;
        padding-right: 1;
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
        self._todo_containers: dict[str, tuple] = {}
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
            yield Static("Ctrl+Enter to submit", id="input-hint")
            yield SubmittableTextArea(id="user-input")
    def create_agent_container(self, log_id, tool_results_id, agent_id):
        chat_scroll = VerticalScroll(Static("", id=log_id), id=f"{log_id}-scroll", classes="left-panel-top")
        todo = Markdown(self._load_todos(agent_id), id=f"{log_id}-todos")
        secondary_scroll = VerticalScroll(todo, id=f"{log_id}-secondary", classes="left-panel-bottom")

        left_panel = ResizableVertical(chat_scroll, secondary_scroll, id="left-panel")

        todo_content = self._load_todos(agent_id)
        if not todo_content:
            secondary_scroll.styles.display = "none"
            left_panel.splitter.styles.display = "none"

        self._todo_containers[str(agent_id)] = (secondary_scroll, left_panel.splitter)

        right_panel = VerticalScroll(id=tool_results_id)
        self._tool_result_collapsibles[tool_results_id] = []
        self._agent_panel_ids[agent_id] = (log_id, tool_results_id)
        self._tool_results_to_agent[tool_results_id] = agent_id
        self._todo_widgets[str(agent_id)] = todo
        self._pending_tool_calls[tool_results_id] = {}
        return ResizableHorizontal(left_panel, right_panel, id="tab-content")

    def on_mount(self) -> None:
        self.query_one("#user-input", TextArea).focus()

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
        if event.key == "ctrl+enter":
            self.action_submit_input()
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

    def action_submit_input(self) -> None:
        text_area = self.query_one("#user-input", TextArea)
        content = text_area.text.strip()
        if self.user_input:
            self.user_input.submit_input(content)
        text_area.clear()

    def write_message(self, log_id: str, message: str) -> None:
        try:
            container = self.query_one(f"#{log_id}", Static)
            current = str(container.render())
            new_content = f"{current}\n{message}" if current else message
            container.update(new_content)
            self.query_one(f"#{log_id}-scroll", VerticalScroll).scroll_end(animate=False)
        except NoMatches:
            logger.warning("Could not find log container #%s", log_id)

    def write_tool_call(self, tool_results_id: str, call_id: str, message: str) -> None:
        pending_for_panel = self._pending_tool_calls.setdefault(tool_results_id, {})
        if "write-todos" in message:
            pending_for_panel.pop(call_id, None)
            self._suppressed_tool_calls.add(call_id)
            return
        try:
            container = self.query_one(f"#{tool_results_id}", VerticalScroll)
        except NoMatches:
            logger.warning("Could not find tool results container #%s", tool_results_id)
            return
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
        pending_entry = pending_for_panel.pop(call_id, None)
        if pending_entry is None:
            logger.warning(
                "Tool result received with no matching call. tool_results_id=%s call_id=%s",
                tool_results_id,
                call_id,
            )
            self._refresh_todos(tool_results_id)
            return
        title_source, text_area, call_collapsible = pending_entry
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
            try:
                contents = call_collapsible.query_one(Collapsible.Contents)
                contents.mount(diff_widget)
            except NoMatches:
                logger.warning(
                    "Missing collapsible contents for tool result. tool_results_id=%s call_id=%s",
                    tool_results_id,
                    call_id,
                )
                call_collapsible.mount(diff_widget)
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
        self._todo_containers.pop(str(agent_id), None)

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
        todo_content = self._load_todos(agent_id)
        todo_widget.update(todo_content)

        container_tuple = self._todo_containers.get(str(agent_id))
        if container_tuple:
            secondary_scroll, splitter = container_tuple
            if todo_content:
                secondary_scroll.styles.display = "block"
                splitter.styles.display = "block"
            else:
                secondary_scroll.styles.display = "none"
                splitter.styles.display = "none"

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

    def on_update_tab_title_message(self, message: UpdateTabTitleMessage) -> None:
        tab_id, _, _ = self.panel_ids_for(message.agent_id)
        try:
            tabs = self.query_one("#tabs", TabbedContent)
            tab = tabs.get_tab(tab_id)
            if tab:
                tab.label = message.title
        except (NoMatches, Exception):
            pass

    def on_refresh_todos_message(self, message: RefreshTodosMessage) -> None:
        self._refresh_todos_for_agent(message.agent_id)
