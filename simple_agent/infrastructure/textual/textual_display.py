from simple_agent.application.display import Display
from simple_agent.application.tool_library import ToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_messages import RefreshTodosMessage, UserSaysMessage, AssistantSaysMessage, ToolCallMessage, ToolResultMessage, SessionStatusMessage

class TextualDisplay(Display):

    def __init__(self, agent_id: str, app: TextualApp, agent_name: str | None = None):
        self.agent_id = agent_id
        self.agent_name = agent_name or agent_id
        self.agent_prefix = f"{self.agent_name}: "
        self.app = app

    def user_says(self, message):
        if self.app and self.app.is_running:
            self.app.post_message(UserSaysMessage("log", f"\nUser: {message}"))

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines and self.app and self.app.is_running:
            self.app.post_message(AssistantSaysMessage(
                "log", 
                f"\n{self.agent_prefix}{lines[0]}",
                is_first_line=True
            ))
            for line in lines[1:]:
                self.app.post_message(AssistantSaysMessage("log", line, is_first_line=False))

    def tool_call(self, call_id, tool):
        if self.app and self.app.is_running:
            self.app.post_message(ToolCallMessage("tool-results", call_id, str(tool)))

    def tool_result(self, call_id, result: ToolResult):
        if not result:
            return
        if self.app and self.app.is_running:
            self.app.post_message(ToolResultMessage("tool-results", call_id, result))

    def continue_session(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage("log", "Continuing session"))

    def start_new_session(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage("log", "Starting new session"))
            self.refresh_todos()

    def refresh_todos(self):
        if self.app and self.app.is_running:
            self.app.post_message(RefreshTodosMessage(self.agent_id))

    def waiting_for_input(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage("log", "\nWaiting for user input..."))

    def interrupted(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage("log", "\n[Session interrupted by user]"))

    def exit(self):
        if self.app and self.app.is_running:
            self.app.post_message(SessionStatusMessage("log", "\nExiting..."))
        self.app.shutdown()
