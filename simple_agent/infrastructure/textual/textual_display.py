from simple_agent.application.display import Display
from simple_agent.application.tool_library import ToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import RefreshTodosMessage, UserSaysMessage, AssistantSaysMessage, ToolCallMessage, ToolResultMessage, SessionStatusMessage

class TextualDisplay(Display):

    def __init__(self, app: TextualApp, agent_id: str, agent_name: str | None = None):
        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id
        self.agent_prefix = f"{self.agent_name}: "
        self.app = app
        _, self.log_id, self.tool_results_id = TextualApp.panel_ids_for(agent_id)

    def user_says(self, message):
        if self.app and self.app.is_running:
            self.app.post_message(UserSaysMessage(self.log_id, f"\nUser: {message}"))

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines and self.app and self.app.is_running:
            self.app.post_message(AssistantSaysMessage(
                self.log_id,
                f"\n{self.agent_prefix}{lines[0]}",
                is_first_line=True
            ))
            for line in lines[1:]:
                self.app.post_message(AssistantSaysMessage(self.log_id, line, is_first_line=False))

    def tool_call(self, call_id, tool):
        if self.app and self.app.is_running:
            self.app.post_message(ToolCallMessage(self.tool_results_id, call_id, str(tool)))

    def tool_result(self, call_id, result: ToolResult):
        if not result:
            return
        if self.app and self.app.is_running:
            self.app.post_message(ToolResultMessage(self.tool_results_id, call_id, result))

    def continue_session(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage(self.log_id, "Continuing session"))

    def start_new_session(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage(self.log_id, "Starting new session"))
            self.refresh_todos()

    def refresh_todos(self):
        if self.app and self.app.is_running:
            self.app.post_message(RefreshTodosMessage(self.agent_id))

    def waiting_for_input(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage(self.log_id, "\nWaiting for user input..."))

    def interrupted(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage(self.log_id, "\n[Session interrupted by user]"))

    def exit(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage(self.log_id, "\nExiting..."))
        self.app.shutdown()
