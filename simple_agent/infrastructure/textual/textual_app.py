import asyncio
import logging
from typing import Callable, Coroutine, Any

logger = logging.getLogger(__name__)

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import TabbedContent

from simple_agent.application.agent_id import AgentId
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.infrastructure.textual.textual_messages import DomainEventMessage
from simple_agent.infrastructure.native_file_searcher import NativeFileSearcher
from simple_agent.infrastructure.textual.smart_input import SmartInput
from simple_agent.infrastructure.textual.widgets.agent_tabs import AgentTabs
from simple_agent.infrastructure.textual.widgets.file_loader import DiskFileLoader, XmlFormattingFileLoader
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    TriggeredSuggestionProvider, SuggestionProvider, CompositeSuggestionProvider
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.slash_commands import (
    SlashAtStartOfLineTrigger, SlashCommandProvider
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.file_search import (
    AtSymbolTrigger, FileSearchProvider
)

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
        dock: bottom;
    }

    #input-hint {
        height: 1;
        color: $text-muted;
        text-align: right;
        padding-right: 1;
    }
    """

    def __init__(self, user_input=None, root_agent_id: AgentId | None = None):
        super().__init__()
        self.user_input = user_input
        self._root_agent_id = root_agent_id or AgentId("Agent")
        self._session_runner: Callable[[], Coroutine[Any, Any, None]] | None = None
        self._session_task: asyncio.Task | None = None
        self._slash_command_registry = SlashCommandRegistry()
        self._file_searcher = NativeFileSearcher()
        self.file_loader = XmlFormattingFileLoader(DiskFileLoader())

    def has_agent_tab(self, agent_id: AgentId) -> bool:
        return self.query_one(AgentTabs).has_agent_tab(agent_id)

    @staticmethod
    def panel_ids_for(agent_id: AgentId) -> tuple[str, str, str]:
        return AgentTabs.panel_ids_for(agent_id)

    def compose(self) -> ComposeResult:
        provider = CompositeSuggestionProvider([
            TriggeredSuggestionProvider(
                trigger=SlashAtStartOfLineTrigger(),
                provider=SlashCommandProvider(self._slash_command_registry)
            ),
            TriggeredSuggestionProvider(
                trigger=AtSymbolTrigger(),
                provider=FileSearchProvider(self._file_searcher)
            )
        ])
        with Vertical():
            yield AgentTabs(self._root_agent_id, id="tabs")
            yield SmartInput(provider=provider, id="user-input")

    async def on_mount(self) -> None:
        smart_input = self.query_one(SmartInput)
        smart_input.focus()
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
        self.query_one(AgentTabs).switch_tab(-1)

    def action_next_tab(self) -> None:
        self.query_one(AgentTabs).switch_tab(1)

    def action_submit_input(self) -> None:
        self.query_one(SmartInput).submit()

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
