import sys

from .chat import Chat
from .session_storage import SessionStorage


class Agent:

    def __init__(self, chat: Chat, system_prompt, input_feed, tools, display, session_storage: SessionStorage):
        self.chat: Chat = chat
        self.system_prompt = system_prompt
        self.input_feed = input_feed
        self.display = display
        self.tools = tools
        self.session_storage = session_storage

    def start(self, messages, rounds=999999):
        result = ""
        for _ in range(rounds):
            try:
                user_input = self.input_feed.read()
                if user_input:
                    messages.user_says(user_input)
                else:
                    self.display.exit()
                    return result
                answer = self.chat(self.system_prompt, messages.to_list())
                self.display.assistant_says(answer)
                messages.assistant_says(answer)

                if self._check_for_escape():
                    user_input = self.input_feed.read()
                    if user_input:
                        messages.user_says(user_input)

                tool = self.tools.parse_tool(answer)

                if tool:
                    self.display.tool_about_to_execute(tool)
                    tool_result = self.tools.execute_parsed_tool(tool)
                    self.display.tool_result(tool_result)
                    if tool.is_completing():
                        result = tool_result
                    else:
                        self.input_feed.stack("Result of " + str(tool) + "\n" + tool_result)

            except (EOFError, KeyboardInterrupt):
                self.display.exit()
                break
        return ""

    @staticmethod
    def _check_for_escape():
        if sys.platform == "win32":
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\x1b':  # ESC key
                    return True
        return False
