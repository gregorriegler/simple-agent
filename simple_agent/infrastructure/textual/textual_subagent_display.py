from simple_agent.infrastructure.textual.textual_display import TextualDisplay


class TextualSubagentDisplay(TextualDisplay):
    def __init__(self, parent_app, agent_id: str, agent_name: str, display_event_handler):
        super().__init__("Subagent")
        self.app = parent_app
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.display_event_handler = display_event_handler
        self.log_id = None
        self.tool_results_id = None
        self._create_tab()

    def _create_tab(self):
        if self.app and self.app.is_running:
            tab_title = self.agent_name or self.agent_id.split('/')[-1]
            self.log_id, self.tool_results_id = self.app.call_from_thread(
                self.app.add_subagent_tab,
                self.agent_id,
                tab_title
            )

    def user_says(self, message):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_message, self.log_id, f"User: {message}\n")

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines and self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_message, self.log_id, f"{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.app.call_from_thread(self.app.write_message, self.log_id, line)
            self.app.call_from_thread(self.app.write_message, self.log_id, "")

    def tool_call(self, tool):
        if self.app and self.app.is_running and self.tool_results_id:
            self.app.call_from_thread(self.app.write_tool_call, self.tool_results_id, str(tool))

    def tool_result(self, result):
        if not result:
            return
        if self.app and self.app.is_running and self.tool_results_id:
            self.app.call_from_thread(self.app.write_tool_result, self.tool_results_id, str(result))

    def continue_session(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_message, self.log_id, "Continuing session")

    def start_new_session(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_message, self.log_id, "Starting new session")

    def waiting_for_input(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_message, self.log_id, "Waiting for user input...\n")

    def interrupted(self):
        if self.app and self.app.is_running and self.log_id:
            self.app.call_from_thread(self.app.write_message, self.log_id, "[Session interrupted by user]\n")

    def exit(self):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.remove_subagent_tab, self.agent_id)
        del self.display_event_handler.displays[self.agent_id]
