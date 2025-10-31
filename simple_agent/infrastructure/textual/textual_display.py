from simple_agent.application.display import Display
from simple_agent.application.tool_library import ToolResult
from simple_agent.infrastructure.textual.textual_app import TextualApp


class TextualDisplay(Display):

    def __init__(self, agent_name: str, app: TextualApp):
        self.agent_name = agent_name
        self.agent_prefix = f"{agent_name}: "
        self.app = app

    def user_says(self, message):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_message, "log", f"\nUser: {message}")

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines and self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_message, "log", f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.app.call_from_thread(self.app.write_message, "log", line)

    def tool_call(self, tool):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_tool_call, "tool-results", str(tool))

    def tool_result(self, result: ToolResult):
        if not result:
            return
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_tool_result, "tool-results", result)

    def continue_session(self):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_message, "log", "Continuing session")

    def start_new_session(self):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_message, "log", "Starting new session")

    def waiting_for_input(self):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_message, "log", "\nWaiting for user input...")

    def interrupted(self):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_message, "log", "\n[Session interrupted by user]")

    def exit(self):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_message, "log", "\nExiting...")
        self.app.shutdown()