from simple_agent.application.agent_id import AgentId
from simple_agent.application.display import AgentDisplay
from simple_agent.infrastructure.display_hub import AgentDisplayHub
from simple_agent.application.tool_library import ToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp
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


class TextualDisplay(AgentDisplayHub):

    def __init__(self, app):
        super().__init__()
        self._app = app

    def _create_display(self, agent_id: AgentId, agent_name: str | None) -> 'TextualAgentDisplay':
        return TextualAgentDisplay(self, self._app, agent_id, agent_name)

    def _on_agent_removed(self, agent_id: AgentId, agent: AgentDisplay) -> None:
        self.remove_tab(agent_id)

    def remove_tab(self, agent_id: AgentId) -> None:
        agent = self._agents.pop(agent_id, None)
        if agent:
            agent._close_tab()


class TextualAgentDisplay(AgentDisplay):

    def __init__(self, hub: TextualDisplay, app: TextualApp, agent_id: AgentId, agent_name: str | None = None):
        self._hub = hub
        self._app = app
        self._agent_id = agent_id
        self._agent_name = agent_name or str(agent_id)
        self._exited = False
        _, self._log_id, self._tool_results_id = TextualApp.panel_ids_for(agent_id)
        self._ensure_tab_exists()

    def _ensure_tab_exists(self) -> None:
        if not self._app or not self._app.is_running:
            return
        if getattr(self._app, "has_agent_tab", None) and self._app.has_agent_tab(self._agent_id):
            return
        tab_title = self._agent_name or str(self._agent_id).split('/')[-1]
        self._app.post_message(AddSubagentTabMessage(self._agent_id, tab_title))

    def user_says(self, message):
        if self._app and self._app.is_running:
            self._app.post_message(UserSaysMessage(self._log_id, f"\nUser: {message}"))

    def assistant_says(self, message):
        lines = str(message).split("\n")
        if not (lines and self._app and self._app.is_running):
            return
        self._app.post_message(
            AssistantSaysMessage(self._log_id, f"\n{self._agent_name}: {lines[0]}", is_first_line=True)
        )
        for line in lines[1:]:
            self._app.post_message(AssistantSaysMessage(self._log_id, line, is_first_line=False))

    def tool_call(self, call_id, tool):
        if self._app and self._app.is_running:
            self._app.post_message(ToolCallMessage(self._tool_results_id, call_id, str(tool)))

    def tool_result(self, call_id, result: ToolResult):
        if not result:
            return
        if self._app and self._app.is_running:
            self._app.post_message(ToolResultMessage(self._tool_results_id, call_id, result))

    def continue_session(self):
        if self._app and self._app.is_running:
            self._app.post_message(SessionStatusMessage(self._log_id, "Continuing session"))

    def start_new_session(self):
        if self._app and self._app.is_running:
            self._app.post_message(SessionStatusMessage(self._log_id, "Starting new session"))
            self.refresh_todos()

    def refresh_todos(self):
        if self._app and self._app.is_running:
            self._app.post_message(RefreshTodosMessage(self._agent_id))

    def waiting_for_input(self):
        if self._app and self._app.is_running:
            self._app.post_message(SessionStatusMessage(self._log_id, "\nWaiting for user input..."))

    def interrupted(self):
        if self._app and self._app.is_running:
            self._app.post_message(SessionStatusMessage(self._log_id, "\n[Session interrupted by user]"))

    def exit(self):
        self._hub.remove_tab(self._agent_id)

    def _close_tab(self) -> None:
        if self._exited:
            return
        self._exited = True
        if self._app and self._app.is_running:
            if getattr(self._app, "has_agent_tab", None) and not self._app.has_agent_tab(self._agent_id):
                return
            self._app.post_message(RemoveAgentTabMessage(self._agent_id))
