import logging
from collections.abc import Callable, Coroutine
from typing import Any

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.native_file_searcher import NativeFileSearcher
from simple_agent.infrastructure.textual.smart_input import SmartInput
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    CompositeSuggestionProvider,
    TriggeredSuggestionProvider,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.file_search import (
    AtSymbolTrigger,
    FileSearchProvider,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.slash_commands import (
    SlashAtStartOfLineTrigger,
    SlashCommandArgumentProvider,
    SlashCommandArgumentTrigger,
    SlashCommandProvider,
)
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
from simple_agent.infrastructure.textual.widgets.file_loader import (
    DiskFileLoader,
    XmlFormattingFileLoader,
)

logger = logging.getLogger(__name__)


class TextualApp(App):
    async def run_with_session_async(
        self, session_runner: Callable[[], Coroutine[Any, Any, None]]
    ):
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

    def __init__(
        self,
        user_input,
        root_agent_id: AgentId,
        agent_task_manager: AgentTaskManager,
        available_models: list[str] | None = None,
    ):
        super().__init__()
        self.user_input = user_input
        self._root_agent_id = root_agent_id
        self.agent_task_manager = agent_task_manager
        self._session_runner: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._slash_command_registry = SlashCommandRegistry(
            available_models=available_models
        )
        self._file_searcher = NativeFileSearcher()
        self.file_loader = XmlFormattingFileLoader(DiskFileLoader())
        self._suggestion_provider = self._create_suggestion_provider()

    def has_agent_tab(self, agent_id: AgentId) -> bool:
        return self.query_one(AgentTabs).has_agent_tab(agent_id)

    @staticmethod
    def panel_ids_for(agent_id: AgentId) -> tuple[str, str, str]:
        return AgentTabs.panel_ids_for(agent_id)

    def _create_suggestion_provider(self):
        return CompositeSuggestionProvider(
            [
                TriggeredSuggestionProvider(
                    trigger=SlashAtStartOfLineTrigger(),
                    provider=SlashCommandProvider(self._slash_command_registry),
                ),
                TriggeredSuggestionProvider(
                    trigger=SlashCommandArgumentTrigger(),
                    provider=SlashCommandArgumentProvider(self._slash_command_registry),
                ),
                TriggeredSuggestionProvider(
                    trigger=AtSymbolTrigger(),
                    provider=FileSearchProvider(self._file_searcher),
                ),
            ]
        )

    def compose(self) -> ComposeResult:
        with Vertical():
            yield AgentTabs(self._suggestion_provider, self._root_agent_id, id="tabs")

    async def on_mount(self) -> None:
        # Focus the smart input of the active tab
        # AgentTabs is mounted, and it should have created the initial tab/workspace
        try:
            tabs = self.query_one(AgentTabs)
            workspace = tabs.active_workspace
            if workspace and workspace.smart_input:
                workspace.smart_input.focus()
        except Exception as e:
            logger.warning("Could not focus smart input on mount: %s", e)

        if self._session_runner:
            self.agent_task_manager.start_task(self._root_agent_id, self._run_session())

    async def _run_session(self) -> None:
        """Run the session and exit the app when done."""
        if self._session_runner is None:
            return
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
            try:
                workspace = self.query_one(AgentTabs).active_workspace
                if workspace:
                    self.agent_task_manager.cancel_task(workspace.agent_id)
            except Exception:
                # Fallback to canceling root if tabs not ready or other error
                self.agent_task_manager.cancel_task(self._root_agent_id)
            event.prevent_default()
            return
        # Enter is now handled by SubmittableTextArea
        return

    async def action_quit(self) -> None:
        """Ensure Ctrl+C / Ctrl+Q stop the agent, not just the UI."""
        if self.user_input:
            self.user_input.close()
        self.agent_task_manager.cancel_all_tasks()
        self.exit()

    def action_previous_tab(self) -> None:
        self.query_one(AgentTabs).switch_tab(-1)

    def action_next_tab(self) -> None:
        self.query_one(AgentTabs).switch_tab(1)

    def action_submit_input(self) -> None:
        """Called when Enter is pressed and handled by binding."""
        # Find active smart input
        try:
            workspace = self.query_one(AgentTabs).active_workspace
            if workspace and workspace.smart_input:
                workspace.smart_input.submit()
        except Exception:
            pass

    def on_smart_input_submitted(self, event: SmartInput.Submitted) -> None:
        if self.user_input:
            expanded_content = event.result.expand(self.file_loader)
            self.user_input.submit_input(expanded_content)

    def add_subagent_tab(self, agent_id: AgentId, tab_title: str) -> tuple[str, str]:
        return self.query_one(AgentTabs).add_subagent_tab(agent_id, tab_title)

    def remove_subagent_tab(self, agent_id: AgentId) -> None:
        self.query_one(AgentTabs).remove_subagent_tab(agent_id)

    def update_tab_title(self, agent_id: AgentId, title: str) -> None:
        self.query_one(AgentTabs).update_tab_title(agent_id, title)

    def on_domain_event_message(self, message: DomainEventMessage) -> None:
        self.query_one(AgentTabs).handle_event(message.event)
