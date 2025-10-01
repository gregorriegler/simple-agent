from .llm import LLM
from .session_storage import SessionStorage


class Agent:

    def __init__(self, llm: LLM, system_prompt, user_input, tools, display, session_storage: SessionStorage):
        self.llm: LLM = llm
        self.system_prompt = system_prompt
        self.user_input = user_input
        self.display = display
        self.tools = tools
        self.session_storage = session_storage
        self._result = ""

    def start(self, context, rounds=999999):
        self._result = ""
        for _ in range(rounds):
            try:
                user_message = self.user_input.read()
            except (EOFError, KeyboardInterrupt):
                self.display.exit()
                break

            if not user_message:
                self.display.exit()
                return self._result

            context.user_says(user_message)
            answer = self.llm(self.system_prompt, context.to_list())
            self.display.assistant_says(answer)
            context.assistant_says(answer)

            if self.user_input.escape_requested():
                escape_message = self.user_input.read()
                if escape_message:
                    context.user_says(escape_message)
                break

            tool = self.tools.parse_tool(answer)
            if not tool:
                continue

            self._handle_tool(tool)

        return self._result

    def _handle_tool(self, tool):
        tool_result = self.tools.execute_parsed_tool(tool)
        self.display.tool_result(tool_result)
        if tool.is_completing():
            self._result = tool_result
            return
        self.user_input.stack("Result of " + str(tool) + "\n" + tool_result)

