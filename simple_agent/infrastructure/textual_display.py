import threading

from simple_agent.application.display import Display
from simple_agent.infrastructure.textual_app import TextualApp


class TextualDisplay(Display):

    def __init__(self, agent_name="Agent", user_input=None):
        self.agent_name = agent_name
        self.agent_prefix = f"{agent_name}: "
        self.user_input = user_input
        self.app: TextualApp | None = None
        self.app_thread: threading.Thread | None = None

    def _ensure_app_running(self):
        if self.app is None:
            self.app = TextualApp(self.user_input)
            self.app_thread = threading.Thread(target=self._run_app)
            self.app_thread.start()
            import time
            time.sleep(0.5)

    def _run_app(self):
        if self.app:
            self.app.run()

    def user_says(self, message):
        self._ensure_app_running()
        if self.app:
            self.app.call_from_thread(self.app.write_message, f"\nUser: {message}")

    def assistant_says(self, message):
        self._ensure_app_running()
        lines = str(message).split('\n')
        if lines and self.app:
            self.app.call_from_thread(self.app.write_message, f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                self.app.call_from_thread(self.app.write_message, line)

    def tool_call(self, tool):
        self._ensure_app_running()
        if self.app:
            self.app.call_from_thread(self.app.write_tool_result, str(tool) + "\n---")

    def tool_result(self, result):
        self._ensure_app_running()
        if not result:
            return
        lines = str(result).split('\n')
        if self.app:
            for line in lines:
                self.app.call_from_thread(self.app.write_tool_result, line + "\n---")

    def continue_session(self):
        self._ensure_app_running()
        if self.app:
            self.app.call_from_thread(self.app.write_message, "Continuing session")

    def start_new_session(self):
        self._ensure_app_running()
        if self.app:
            self.app.call_from_thread(self.app.write_message, "Starting new session")

    def exit(self):
        if self.app and self.app.is_running:
            self.app.call_from_thread(self.app.write_message, "\nExiting...")
            self.app.call_from_thread(self.app.exit)
            if self.app_thread and self.app_thread.is_alive():
                self.app_thread.join(timeout=2.0)


