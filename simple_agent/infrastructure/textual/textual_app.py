import asyncio
import logging
import re
from pathlib import Path
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

from rich.syntax import Syntax
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.timer import Timer
from textual.containers import Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.geometry import Offset, Size
from textual.widgets import Static, TabbedContent, TabPane, TextArea, Collapsible, Markdown

from simple_agent.application.agent_id import AgentId
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    ErrorEvent,
    SessionClearedEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolCancelledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.application.tool_results import ToolResult
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from simple_agent.infrastructure.textual.resizable_container import ResizableHorizontal, ResizableVertical
from simple_agent.application.file_search import FileSearcher
from simple_agent.infrastructure.native_file_searcher import NativeFileSearcher
from simple_agent.infrastructure.textual.widgets.smart_input import SubmittableTextArea, AutocompletePopup
from simple_agent.infrastructure.textual.widgets.todo_view import TodoView
from simple_agent.infrastructure.textual.widgets.chat_log import ChatLog
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog

class TextualApp(App):

    async def run_with_session_async(self, session_runner: Callable[[], Coroutine[Any, Any, None]]):
        self._session_runner = session_runner
        return await self.run_async()

    def shutdown(self):
        if self.is_running:
            self.exit()
    BINDINGS = [
        ("alt+left", "previous_tab", "Previous Tab"),
        ("alt+right", "next_tab", "Next Tab"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("enter", "submit_input", "Submit"),
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

    .tool-result-success {
        border: round $success;
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
        self._session_runner: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._session_task: asyncio.Task | None = None
        self._agent_panel_ids: dict[AgentId, tuple[str, str]] = {}
        self._agent_names: dict[AgentId, str] = {root_agent_id: root_agent_id.raw}
        self._todo_widgets: dict[str, Markdown] = {}
        self._todo_containers: dict[str, tuple] = {}
        self._tool_results_to_agent: dict[str, AgentId] = {}
        self._slash_command_registry = SlashCommandRegistry()
        self._file_searcher = NativeFileSearcher()
        self._agent_models: dict[AgentId, str] = {root_agent_id: ""}
        self._agent_max_tokens: dict[AgentId, int] = {root_agent_id: 0}

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
            yield Static("Enter to submit, Ctrl+Enter for newline", id="input-hint")
            yield SubmittableTextArea(id="user-input")
            yield AutocompletePopup(id="autocomplete-popup")

    def create_agent_container(self, log_id, tool_results_id, agent_id):
        chat_scroll = ChatLog(id=f"{log_id}-scroll", classes="left-panel-top")
        todo_view = TodoView(agent_id, markdown_id=f"{log_id}-todos", id=f"{log_id}-secondary", classes="left-panel-bottom")

        left_panel = ResizableVertical(chat_scroll, todo_view, id="left-panel")
        left_panel.set_bottom_visibility(todo_view.has_content)

        self._todo_containers[str(agent_id)] = left_panel

        def refresh_todos_callback():
            self._refresh_todos(tool_results_id)

        right_panel = ToolLog(id=tool_results_id, on_refresh_todos=refresh_todos_callback)
        self._agent_panel_ids[agent_id] = (log_id, tool_results_id)
        self._tool_results_to_agent[tool_results_id] = agent_id
        self._todo_widgets[str(agent_id)] = todo_view
        return ResizableHorizontal(left_panel, right_panel, id="tab-content")

    async def on_mount(self) -> None:
        text_area = self.query_one("#user-input", SubmittableTextArea)
        text_area.slash_command_registry = self._slash_command_registry
        text_area.file_searcher = self._file_searcher
        text_area.focus()
        if self._session_runner:
            self._session_task = asyncio.create_task(self._run_session())

    async def _run_session(self) -> None:
        """Run the session and exit the app when done."""
        try:
            await self._session_runner()
        except Exception as e:
            logger.error("Session error: %s", e)
        self.exit()

    def on_unmount(self) -> None:
        if self.user_input:
            self.user_input.close()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            if self._session_task and not self._session_task.done():
                self._session_task.cancel()
            event.prevent_default()
            return
        # Enter is now handled by SubmittableTextArea
        return

    def action_quit(self) -> None:
        """Ensure Ctrl+C / Ctrl+Q stop the agent, not just the UI."""
        if self.user_input:
            self.user_input.close()
        if self._session_task and not self._session_task.done():
            self._session_task.cancel()
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
        text_area = self.query_one("#user-input", SubmittableTextArea)
        content = text_area.text.strip()
        
        referenced_files = text_area.get_referenced_files()
        if referenced_files:
            file_contents = []
            for file_path_str in referenced_files:
                try:
                    path = Path(file_path_str)
                    if path.exists() and path.is_file():
                        file_text = path.read_text(encoding="utf-8")
                        file_contents.append(f'<file_context path="{file_path_str}">\n{file_text}\n</file_context>')
                except Exception as e:
                    logger.error(f"Failed to read referenced file {file_path_str}: {e}")
            
            if file_contents:
                content += "\n" + "\n".join(file_contents)
                # Clear references after consuming them
                text_area._referenced_files.clear()

        if self.user_input:
            self.user_input.submit_input(content)
        text_area.clear()
        text_area._hide_autocomplete()

    def write_message(self, log_id: str, message: str) -> None:
        try:
            chat_log = self.query_one(f"#{log_id}-scroll", ChatLog)
            chat_log.write(message)
        except NoMatches:
            logger.warning("Could not find scroll container #%s-scroll", log_id)
        except Exception as e:
            logger.error("Failed to display message: %s. Message: %s", e, message)


    def write_tool_call(self, tool_results_id: str, call_id: str, message: str) -> None:
        try:
            tool_log = self.query_one(f"#{tool_results_id}", ToolLog)
            tool_log.add_tool_call(call_id, message)
        except NoMatches:
            logger.warning("Could not find tool results container #%s", tool_results_id)

    def write_tool_result(self, tool_results_id: str, call_id: str, result: ToolResult) -> None:
        try:
            tool_log = self.query_one(f"#{tool_results_id}", ToolLog)
            tool_log.add_tool_result(call_id, result)
        except NoMatches:
            logger.warning("Could not find tool results container #%s", tool_results_id)

    def write_tool_cancelled(self, tool_results_id: str, call_id: str) -> None:
        try:
            tool_log = self.query_one(f"#{tool_results_id}", ToolLog)
            tool_log.add_tool_cancelled(call_id)
        except NoMatches:
            logger.warning("Could not find tool results container #%s", tool_results_id)

    def add_subagent_tab(self, agent_id: AgentId, tab_title: str) -> tuple[str, str]:
        tab_id, log_id, tool_results_id = self.panel_ids_for(agent_id)

        agent_name = tab_title.split(" [")[0] if " [" in tab_title else tab_title
        self._agent_names[agent_id] = agent_name

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
            self._tool_results_to_agent.pop(tool_results_id, None)
        self._agent_names.pop(agent_id, None)
        self._todo_widgets.pop(str(agent_id), None)
        self._todo_containers.pop(str(agent_id), None)

    def _refresh_todos(self, tool_results_id: str) -> None:
        agent_id = self._tool_results_to_agent.get(tool_results_id)
        if not agent_id:
            return
        self._refresh_todos_for_agent(agent_id)

    def _refresh_todos_for_agent(self, agent_id: AgentId) -> None:
        todo_widget = self._todo_widgets.get(str(agent_id))
        if isinstance(todo_widget, TodoView):
            todo_widget.refresh_content()
            has_content = todo_widget.has_content
        else:
            return

        left_panel = self._todo_containers.get(str(agent_id))
        if left_panel and isinstance(left_panel, ResizableVertical):
            left_panel.set_bottom_visibility(has_content)

    def update_tab_title(self, agent_id: AgentId, title: str) -> None:
        tab_id, _, _ = self.panel_ids_for(agent_id)
        try:
            tabs = self.query_one("#tabs", TabbedContent)
            tab = tabs.get_tab(tab_id)
            if tab:
                tab.label = title
        except (NoMatches, Exception):
            pass

    def _ensure_agent_tab_exists(self, agent_id: AgentId, agent_name: str | None, model: str) -> None:
        if not self.is_running:
            return
        if agent_name:
            self._agent_names[agent_id] = agent_name
        if model is not None:
            self._agent_models[agent_id] = model
        if self.has_agent_tab(agent_id):
            if model:
                title = self._tab_title_for(agent_id, model, 0, self._agent_max_tokens.get(agent_id, 0))
                self.update_tab_title(agent_id, title)
            return
        tab_title = self._tab_title_for(agent_id, model, 0, 0)
        self.add_subagent_tab(agent_id, tab_title)

    def on_domain_event_message(self, message: DomainEventMessage) -> None:
        event = message.event
        if isinstance(event, AgentStartedEvent):
            self._ensure_agent_tab_exists(event.agent_id, event.agent_name, event.model)
        elif isinstance(event, SessionClearedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.clear_agent_panels(log_id)
            self._clear_todo_panel(event.agent_id)
            self._reset_agent_token_usage(event.agent_id)
        elif isinstance(event, UserPromptedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            
            # Compact file context for display
            display_text = event.input_text
            
            # Find all context blocks
            pattern = r'<file_context path="([^"]+)">.*?</file_context>'
            matches = list(re.finditer(pattern, display_text, flags=re.DOTALL))
            
            if matches:
                # Remove all blocks from the text first to get the core message
                core_text = re.sub(pattern, "", display_text, flags=re.DOTALL).strip()
                
                attachments = []
                for match in matches:
                    path = match.group(1)
                    marker = f"[📦{path}]"
                    
                    # If the marker is already in core_text, we don't need to do anything else for this file
                    if marker in core_text:
                        continue
                        
                    # Fallback for manually typed paths or older logic
                    escaped_path = re.escape(path)
                    if re.search(escaped_path, core_text):
                        # Replace the first occurrence of the path with the marker
                        core_text = re.sub(escaped_path, marker, core_text, count=1)
                    else:
                        attachments.append(marker)
                
                display_text = core_text
                if attachments:
                    display_text += "\n" + "\n".join(attachments)
            
            self.write_message(log_id, f"**User:** {display_text}")
        elif isinstance(event, AssistantSaidEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            agent_name = self._agent_names.get(event.agent_id, str(event.agent_id))
            self.write_message(log_id, f"**{agent_name}:** {event.message}")
        elif isinstance(event, ToolCalledEvent):
            _, _, tool_results_id = self.panel_ids_for(event.agent_id)
            self.write_tool_call(tool_results_id, event.call_id, event.tool.header())
        elif isinstance(event, ToolResultEvent):
            if not event.result:
                return
            _, _, tool_results_id = self.panel_ids_for(event.agent_id)
            self.write_tool_result(tool_results_id, event.call_id, event.result)
        elif isinstance(event, ToolCancelledEvent):
            _, _, tool_results_id = self.panel_ids_for(event.agent_id)
            self.write_tool_cancelled(tool_results_id, event.call_id)
        elif isinstance(event, SessionInterruptedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.write_message(log_id, "\n[Session interrupted by user]")
        elif isinstance(event, SessionStartedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            if event.is_continuation:
                self.write_message(log_id, "Continuing session")
            else:
                self.write_message(log_id, "Starting new session")
        elif isinstance(event, SessionEndedEvent):
            if self.is_running and self.has_agent_tab(event.agent_id):
                self.remove_subagent_tab(event.agent_id)
        elif isinstance(event, UserPromptRequestedEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.write_message(log_id, "\nWaiting for user input...")
        elif isinstance(event, ErrorEvent):
            _, log_id, _ = self.panel_ids_for(event.agent_id)
            self.write_message(log_id, f"\n**❌ Error: {event.message}**")
        elif isinstance(event, AssistantRespondedEvent):
            self._agent_models[event.agent_id] = event.model
            self._agent_max_tokens[event.agent_id] = event.max_tokens
            title = self._tab_title_for(event.agent_id, event.model, event.token_count, event.max_tokens)
            self.update_tab_title(event.agent_id, title)

    def _tab_title_for(self, agent_id: AgentId, model: str, token_count: int, max_tokens: int) -> str:
        base_title = self._agent_names.get(agent_id, str(agent_id))

        if not model:
            return base_title

        if max_tokens == 0:
            return f"{base_title} [{model}: 0.0%]"

        percentage = (token_count / max_tokens) * 100
        return f"{base_title} [{model}: {percentage:.1f}%]"

    def clear_agent_panels(self, log_id: str) -> None:
        # Clear chat scroll area
        try:
            chat_scroll = self.query_one(f"#{log_id}-scroll", ChatLog)
            chat_scroll.remove_children()
        except NoMatches:
            logger.warning("Could not find chat scroll #%s-scroll to clear", log_id)

        # Clear tool results panel
        tool_results_id = log_id.replace("log-", "tool-results-")
        try:
            tool_results = self.query_one(f"#{tool_results_id}", ToolLog)
            tool_results.clear()
        except NoMatches:
            logger.warning("Could not find tool results #%s to clear", tool_results_id)

    def _clear_todo_panel(self, agent_id: AgentId) -> None:
        todo_widget = self._todo_widgets.get(str(agent_id))
        if isinstance(todo_widget, TodoView):
            # We can't easily clear the file, but we can clear the view representation
            # Actually, `SessionClearedEvent` implies we want to clear the session state.
            # But todo files are persistent. The original code just updated the widget to empty.
            # However, if TodoView reads from file on refresh, we might have an inconsistency
            # if we just update the widget but not the file.
            # The original code: `todo_widget.update("")` and hidden it.
            # Let's replicate that behavior by forcing it to hide.
            todo_widget.update("")
            # Also, we might want to manually set visibility to hidden
            left_panel = self._todo_containers.get(str(agent_id))
            if left_panel and isinstance(left_panel, ResizableVertical):
                left_panel.set_bottom_visibility(False)

    def _reset_agent_token_usage(self, agent_id: AgentId) -> None:
        model = self._agent_models.get(agent_id, "")
        max_tokens = self._agent_max_tokens.get(agent_id, 0)
        title = self._tab_title_for(agent_id, model, 0, max_tokens)
        self.update_tab_title(agent_id, title)
