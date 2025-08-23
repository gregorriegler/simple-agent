from chat import save_chat
from tools import ToolLibrary
from abc import ABC, abstractmethod

class Display(ABC):

    @abstractmethod
    def assistant_says(self, message):
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

    def __init__(self, system_prompt, message_claude, display, save_chat=save_chat):
        self.system_prompt = system_prompt
        self.message_claude = message_claude
        self.display = display
        self.save_chat = save_chat

    def start(self, chat, rounds=999999):
        tools = ToolLibrary()

        for _ in range(rounds):
            answer = self.message_claude(chat.to_list(), self.system_prompt)
            self.display.assistant_says(answer)
            chat.assistant_says(answer)

            try:
                user_input = self.display.input()
                if user_input.strip():
                    chat.user_says(user_input)
                    continue
            except (EOFError, KeyboardInterrupt):
                self.display.exit()
                break

            tool_result = tools.parse_and_execute(answer)
            self.display.tool_result(tool_result)

            if tool_result:
                chat.user_says(tool_result)

            self.save_chat(chat)
