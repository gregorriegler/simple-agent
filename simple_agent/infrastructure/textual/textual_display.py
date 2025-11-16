from simple_agent.application.display import AgentDisplay, Display
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


class TextualDisplay(Display):

    def __init__(self, app):
        self._app = app
        self._agents: dict[str, TextualAgentDisplay] = {}

    def create_agent_tab(self, agent_id: str, agent_name: str | None = None) -> 'TextualAgentDisplay':
        existing = self._agents.get(agent_id)
        if existing:
            return existing
        agent_display = TextualAgentDisplay(self, self._app, agent_id, agent_name)
        self._agents[agent_id] = agent_display
        return agent_display

    def agent_created(self, event) -> None:
        if event.subagent_id in self._agents:
            return
        self.create_agent_tab(event.subagent_id, event.subagent_name)

    def start_session(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if not agent:
            return
        if getattr(event, "is_continuation", False):
            agent.continue_session()
        else:
            agent.start_new_session()

    def wait_for_input(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if agent:
            agent.waiting_for_input()

    def user_says(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if agent:
            agent.user_says(event.input_text)

    def assistant_says(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if agent:
            agent.assistant_says(event.message)

    def tool_call(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if agent:
            agent.tool_call(event.call_id, event.tool)

    def tool_result(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if agent:
            agent.tool_result(event.call_id, event.result)

    def interrupted(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if agent:
            agent.interrupted()

    def exit(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if agent:
            agent.exit()

    def _agent_for(self, agent_id: str) -> 'TextualAgentDisplay | None':
        return self._agents.get(agent_id)

    def remove_tab(self, agent_id: str) -> None:
        agent = self._agents.pop(agent_id, None)
        if agent:
            agent._close_tab()


class TextualAgentDisplay(AgentDisplay):

    def __init__(self, hub: TextualDisplay, app: TextualApp, agent_id: str, agent_name: str | None = None):
        self._hub = hub
        self._app = app
        self._agent_id = agent_id
        self._agent_name = agent_name or agent_id
        self._exited = False
        _, self._log_id, self._tool_results_id = TextualApp.panel_ids_for(agent_id)
        self._ensure_tab_exists()

    def _ensure_tab_exists(self) -> None:
        if not self._app or not self._app.is_running:
            return
        if getattr(self._app, "has_agent_tab", None) and self._app.has_agent_tab(self._agent_id):
            return
        tab_title = self._agent_name or self._agent_id.split('/')[-1]
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
