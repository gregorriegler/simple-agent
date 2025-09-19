import sys

from .chat import Chat
from .session_storage import SessionStorage


class Agent:

    def __init__(self, chat: Chat, system_prompt, tools, display, session_storage: SessionStorage):
        self.chat: Chat = chat
        self.system_prompt = system_prompt
        self.display = display
        self.tools = tools
        self.session_storage = session_storage

    def start(self, messages, rounds=999999):
        for _ in range(rounds):
            try:
                answer = self.chat(self.system_prompt, messages.to_list())
                self.display.assistant_says(answer)
                messages.assistant_says(answer)
                self.session_storage.save(messages)

                parsed_tool = self.tools.parse_tool(answer)
                if parsed_tool:
                    tool_result = self.tools.execute_parsed_tool(parsed_tool)
                    if parsed_tool.tool_instance.is_completing():
                        self.session_storage.save(messages)
                        user_input = self.display.input()
                        if not user_input:
                            self.display.exit()
                            return tool_result
                        messages.user_says(user_input)
                    else:
                        self.display.tool_result(tool_result)
                        messages.user_says("Result of " + str(parsed_tool) + "\n" + tool_result)

                self.session_storage.save(messages)

                if not parsed_tool or self._check_for_escape():
                    user_input = self.display.input()
                    if not user_input:
                        self.display.exit()
                        return ""
                    messages.user_says(user_input)
                    self.session_storage.save(messages)


            except (EOFError, KeyboardInterrupt):
                self.display.exit()
                break
        return None

    def _check_for_escape(self):
        if sys.platform == "win32":
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b'\x1b':  # ESC key
                    return True
        return False
