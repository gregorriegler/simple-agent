from chat import save_chat
from abc import ABC, abstractmethod
import sys

class Display(ABC):

    @abstractmethod
    def assistant_says(self, message):
        pass

    @abstractmethod
    def tool_about_to_execute(self, parsed_tool):
        pass

    @abstractmethod
    def tool_result(self, result):
        pass

    @abstractmethod
    def input(self):
        pass

    @abstractmethod
    def exit(self):
        pass

class Agent:

    def __init__(self, system_prompt, message_claude, display, tools, save_chat=save_chat):
        self.system_prompt = system_prompt
        self.message_claude = message_claude
        self.display = display
        self.tools = tools
        self.save_chat = save_chat

    def start(self, chat, rounds=999999):
        for _ in range(rounds):
            try:
                answer = self.message_claude(chat.to_list(), self.system_prompt)
                self.display.assistant_says(answer)
                chat.assistant_says(answer)

                if self._check_for_escape():
                    user_input = self.display.input()
                    if user_input.strip():
                        chat.user_says(user_input)
                        continue

                parsed_tool = self.tools.parse_tool(answer)
                if parsed_tool:
                    #self.display.tool_about_to_execute(parsed_tool)
                    tool_result = self.tools.execute_parsed_tool(parsed_tool)
                    if parsed_tool.tool_instance.is_completing():
                        self.save_chat(chat)
                        self.display.exit()
                        return tool_result
                    self.display.tool_result(tool_result)
                    chat.user_says("Result of " + str(parsed_tool) + "\n" + tool_result)

                self.save_chat(chat)
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
