import logging

from rich.markup import escape
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.widgets import TabbedContent, TabPane

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import (
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    ErrorEvent,
    ModelChangedEvent,
    SessionClearedEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolCancelledEvent,
    ToolResultEvent,
    UserPromptedEvent,
    UserPromptRequestedEvent,
)
from simple_agent.infrastructure.textual.smart_input import SmartInput
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    SuggestionProvider,
)
from simple_agent.infrastructure.textual.widgets.agent_workspace import AgentWorkspace

logger = logging.getLogger(__name__)


class AgentTabs(TabbedContent):
    """
    Manages the tabs for different agents/sub-agents.
    Each tab contains an AgentWorkspace.
    """

    def __init__(
        self, root_agent_id: AgentId, input_provider: SuggestionProvider, **kwargs
    ):
        super().__init__(**kwargs)
        self._root_agent_id = root_agent_id
        self._input_provider = input_provider
        self._agent_panel_ids: dict[AgentId, tuple[str, str]] = {}
        self._agent_tab_ids: dict[AgentId, str] = {}
        self._tab_ids_to_agent: dict[str, AgentId] = {}
        self._agent_names: dict[AgentId, str] = {}
        self._agent_workspaces: dict[str, AgentWorkspace] = {}
        self._agent_inputs: dict[AgentId, SmartInput] = {}
        self._input_ids_to_agent: dict[str, AgentId] = {}
        self._tool_results_to_agent: dict[str, AgentId] = {}
        self._agent_models: dict[AgentId, str] = {}
        self._agent_token_display: dict[AgentId, str] = {}

    def on_mount(self) -> None:
        if not self.has_agent_tab(self._root_agent_id):
            tab_title = self._tab_title_for(self._root_agent_id, "", "")
            self.add_subagent_tab(self._root_agent_id, tab_title)

    @staticmethod
    def panel_ids_for(agent_id: AgentId) -> tuple[str, str, str]:
        sanitized = agent_id.for_ui()
        tab_id = f"tab-{sanitized}"
        log_id = f"log-{sanitized}"
        tool_results_id = f"tool-results-{sanitized}"
        return tab_id, log_id, tool_results_id

    def create_agent_container(self, log_id, tool_results_id, agent_id):
        workspace = AgentWorkspace(
            agent_id=agent_id,
            log_id=log_id,
            tool_results_id=tool_results_id,
            id="tab-content",
        )

        input_id = f"user-input-{agent_id.for_ui()}"
        user_input = SmartInput(
            provider=self._input_provider, id=input_id, classes="user-input"
        )

        self._agent_workspaces[str(agent_id)] = workspace
        self._agent_inputs[agent_id] = user_input
        self._input_ids_to_agent[input_id] = agent_id
        self._agent_panel_ids[agent_id] = (log_id, tool_results_id)
        self._tool_results_to_agent[tool_results_id] = agent_id
        return Vertical(workspace, user_input, id=f"tab-container-{agent_id.for_ui()}")

    def has_agent_tab(self, agent_id: AgentId) -> bool:
        return agent_id in self._agent_panel_ids

    def add_subagent_tab(self, agent_id: AgentId, tab_title: str) -> tuple[str, str]:
        tab_id, log_id, tool_results_id = self.panel_ids_for(agent_id)

        agent_name = tab_title.split(" [")[0] if " [" in tab_title else tab_title
        self._agent_names[agent_id] = agent_name

        new_tab = TabPane(escape(tab_title), id=tab_id)
        new_tab.compose_add_child(
            self.create_agent_container(log_id, tool_results_id, agent_id)
        )

        self._agent_tab_ids[agent_id] = tab_id
        self._tab_ids_to_agent[tab_id] = agent_id
        self.add_pane(new_tab)
        self.active = tab_id
        self.focus_active_input()
        return log_id, tool_results_id

    def remove_subagent_tab(self, agent_id: AgentId) -> None:
        tab_id, _, tool_results_id = self.panel_ids_for(agent_id)
        self.remove_pane(tab_id)
        panel_ids = self._agent_panel_ids.pop(agent_id, None)
        if panel_ids:
            self._tool_results_to_agent.pop(tool_results_id, None)
        input_widget = self._agent_inputs.pop(agent_id, None)
        if input_widget and input_widget.id:
            self._input_ids_to_agent.pop(input_widget.id, None)
        self._tab_ids_to_agent.pop(tab_id, None)
        self._agent_tab_ids.pop(agent_id, None)
        self._agent_names.pop(agent_id, None)
        self._agent_workspaces.pop(str(agent_id), None)

    def update_tab_title(self, agent_id: AgentId, title: str) -> None:
        tab_id, _, _ = self.panel_ids_for(agent_id)
        try:
            tab = self.get_tab(tab_id)
            if tab:
                tab.label = escape(title)
        except (NoMatches, Exception):
            pass

    def switch_tab(self, direction: int) -> None:
        tab_panes = list(self.query(TabPane))
        if len(tab_panes) <= 1:
            return
        current_index = next(
            (i for i, pane in enumerate(tab_panes) if pane.id == self.active), 0
        )
        new_index = (current_index + direction) % len(tab_panes)
        new_tab_id = tab_panes[new_index].id
        if new_tab_id:
            self.active = new_tab_id
            self.focus_active_input()

    def focus_active_input(self) -> None:
        active_input = self.active_input()
        if active_input:
            active_input.focus()

    def active_input(self) -> SmartInput | None:
        agent_id = self._tab_ids_to_agent.get(self.active)
        if agent_id is None:
            return None
        return self._agent_inputs.get(agent_id)

    def agent_id_for_input(self, user_input: SmartInput) -> AgentId | None:
        if user_input.id is None:
            return None
        return self._input_ids_to_agent.get(user_input.id)

    def handle_event(self, event) -> None:
        agent_id = getattr(event, "agent_id", None)
        if agent_id is None:
            return
        if isinstance(event, AgentStartedEvent):
            self._ensure_agent_tab_exists(agent_id, event.agent_name, event.model)
        elif isinstance(event, SessionClearedEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                workspace.clear()
            else:
                logger.warning(
                    "Could not find workspace for agent %s to clear", agent_id
                )
            self._reset_agent_token_usage(agent_id)
        elif isinstance(event, UserPromptedEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                workspace.add_user_message(event.input_text)
            else:
                logger.warning(
                    "Could not find workspace for agent %s to add user message",
                    agent_id,
                )
        elif isinstance(event, AssistantSaidEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                agent_name = self._agent_names.get(agent_id, str(agent_id))
                workspace.add_assistant_message(event.message, agent_name)
            else:
                logger.warning(
                    "Could not find workspace for agent %s to add assistant message",
                    agent_id,
                )
        elif isinstance(event, ToolCalledEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                workspace.on_tool_call(event.call_id, event.tool.header())
            else:
                logger.warning(
                    "Could not find workspace for agent %s to write tool call",
                    agent_id,
                )
        elif isinstance(event, ToolResultEvent):
            if not event.result:
                return
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                workspace.on_tool_result(event.call_id, event.result)
            else:
                logger.warning(
                    "Could not find workspace for agent %s to write tool result",
                    agent_id,
                )
        elif isinstance(event, ToolCancelledEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                workspace.on_tool_cancelled(event.call_id)
            else:
                logger.warning(
                    "Could not find workspace for agent %s to write tool cancelled",
                    agent_id,
                )
        elif isinstance(event, SessionInterruptedEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                workspace.write_message("\n[Session interrupted by user]")
        elif isinstance(event, SessionStartedEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                if event.is_continuation:
                    workspace.write_message("Continuing session")
                else:
                    workspace.write_message("Starting new session")
        elif isinstance(event, SessionEndedEvent):
            if not self.app.is_running:
                return
            if self.has_agent_tab(agent_id):
                self.remove_subagent_tab(agent_id)
        elif isinstance(event, UserPromptRequestedEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                workspace.write_message("\nWaiting for user input...")
        elif isinstance(event, ErrorEvent):
            workspace = self._agent_workspaces.get(str(agent_id))
            if workspace:
                workspace.write_message(f"\n**❌ Error: {event.message}**")
        elif isinstance(event, AssistantRespondedEvent):
            self._agent_models[agent_id] = event.model
            self._agent_token_display[agent_id] = event.token_usage_display
            title = self._tab_title_for(
                agent_id, event.model, event.token_usage_display
            )
            self.update_tab_title(agent_id, title)
        elif isinstance(event, ModelChangedEvent):
            self._agent_models[agent_id] = event.new_model
            token_display = self._agent_token_display.get(agent_id, "")
            title = self._tab_title_for(agent_id, event.new_model, token_display)
            self.update_tab_title(agent_id, title)

    def _ensure_agent_tab_exists(
        self, agent_id: AgentId, agent_name: str | None, model: str
    ) -> None:
        if not self.app.is_running:
            return
        if agent_name:
            self._agent_names[agent_id] = agent_name
        if model is not None:
            self._agent_models[agent_id] = model
        if self.has_agent_tab(agent_id):
            if model:
                token_display = self._agent_token_display.get(agent_id, "")
                if not token_display:
                    token_display = "0.0%"
                    self._agent_token_display[agent_id] = token_display
                title = self._tab_title_for(agent_id, model, token_display)
                self.update_tab_title(agent_id, title)
            return
        initial_token_display = "0.0%" if model else ""
        tab_title = self._tab_title_for(agent_id, model, initial_token_display)
        self.add_subagent_tab(agent_id, tab_title)

    def _tab_title_for(self, agent_id: AgentId, model: str, token_display: str) -> str:
        base_title = self._agent_names.get(agent_id, str(agent_id))

        if not model:
            return base_title

        if not token_display:
            return f"{base_title} [{model}]"

        return f"{base_title} [{model}: {token_display}]"

    def _reset_agent_token_usage(self, agent_id: AgentId) -> None:
        model = self._agent_models.get(agent_id, "")
        self._agent_token_display[agent_id] = ""
        title = self._tab_title_for(agent_id, model, "")
        self.update_tab_title(agent_id, title)
