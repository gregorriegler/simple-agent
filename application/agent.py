from .chat import Chat
from .session_storage import SessionStorage


class Agent:

    def __init__(self, chat: Chat, system_prompt, user_input, tools, display, session_storage: SessionStorage):
        self.chat: Chat = chat
        self.system_prompt = system_prompt
        self.input = user_input
        self.display = display
        self.tools = tools
        self.session_storage = session_storage

    def start(self, messages, rounds=999999):
        result = ""
        for _ in range(rounds):
            try:
                user_input = self.input.read()
                if user_input:
                    messages.user_says(user_input)
                else:
                    self.display.exit()
                    return result
                answer = self.chat(self.system_prompt, messages.to_list())
                self.display.assistant_says(answer)
                messages.assistant_says(answer)

                if self.input.escape_requested():
                    user_input = self.input.read()
                    if user_input:
                        messages.user_says(user_input)

                tool = self.tools.parse_tool(answer)

                if tool:
                    tool_result = self.tools.execute_parsed_tool(tool)
                    self.display.tool_result(tool_result)
                    if tool.is_completing():
                        result = tool_result
                    else:
                        self.input.stack("Result of " + str(tool) + "\n" + tool_result)

            except (EOFError, KeyboardInterrupt):
                self.display.exit()
                break
        return ""

