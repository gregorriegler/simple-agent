from simple_agent.application.tool_library import ToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_display import TextualDisplay
from simple_agent.infrastructure.textual.textual_messages import (
    AddSubagentTabMessage,
    AssistantSaysMessage,
    RemoveSubagentTabMessage,
    SessionStatusMessage,
    ToolCallMessage,
    ToolResultMessage,
    UserSaysMessage,
)


class TextualSubagentDisplay(TextualDisplay):
    def __init__(self, app: TextualApp, agent_id: str, agent_name: str):
        super().__init__(app, agent_id, agent_name)
        self.log_id = None
        self.tool_results_id = None
        self._create_tab()

    def _create_tab(self):
        if self.app and self.app.is_running:
            tab_title = self.agent_name or self.agent_id.split('/')[-1]
            _, self.log_id, self.tool_results_id = TextualApp.panel_ids_for(self.agent_id)
            self.app.post_message(AddSubagentTabMessage(self.agent_id, tab_title))

    def user_says(self, message):
        if self.app and self.app.is_running and self.log_id:
            self.app.post_message(UserSaysMessage(self.log_id, f"User: {message}\n"))

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines and self.app and self.app.is_running and self.log_id:
            self.app.post_message(AssistantSaysMessage(self.log_id, f"{self.agent_prefix}{lines[0]}"))
            for line in lines[1:]:
                self.app.post_message(AssistantSaysMessage(self.log_id, line))
            self.app.post_message(AssistantSaysMessage(self.log_id, ""))

    def tool_call(self, call_id, tool):
        if self.app and self.app.is_running and self.tool_results_id:
            self.app.post_message(ToolCallMessage(self.tool_results_id, call_id, str(tool)))

    def tool_result(self, call_id, result: ToolResult):
        if not result:
            return
        if self.app and self.app.is_running and self.tool_results_id:
            self.app.post_message(ToolResultMessage(self.tool_results_id, call_id, result))

    def continue_session(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.post_message(SessionStatusMessage(self.log_id, "Continuing session"))

    def start_new_session(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.post_message(SessionStatusMessage(self.log_id, "Starting new session"))
            self.refresh_todos()

    def waiting_for_input(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.post_message(SessionStatusMessage(self.log_id, "Waiting for user input...\n"))

    def interrupted(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.post_message(SessionStatusMessage(self.log_id, "[Session interrupted by user]\n"))

    def exit(self):
        if self.app and self.app.is_running:
            self.app.post_message(RemoveSubagentTabMessage(self.agent_id))
