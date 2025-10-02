from .llm import LLM
from .session_storage import SessionStorage
from .tool_result import ToolResult, ContinueResult


class Agent:
    def __init__(self, llm: LLM, system_prompt, user_input, tools, display, session_storage: SessionStorage):
        self.llm: LLM = llm
        self.system_prompt = system_prompt
        self.user_input = user_input
        self.display = display
        self.tools = tools
        self.session_storage = session_storage

    def start(self, context, rounds=999999):
        tool_result: ToolResult = ContinueResult("")
        for _ in range(rounds):
            try:
                user_message = self.handle_user_message(context)
                if not user_message:
                    self.display.exit()
                    return tool_result

                llm_answer = self.handle_llm_answer(context)
                if self.user_input.escape_requested():
                    self.handle_user_message(context)
                    break

                tool = self.tools.parse_tool(llm_answer)
                if tool:
                    tool_result = self.tools.execute_parsed_tool(tool)
                    self.display.tool_result(str(tool_result))
                    if isinstance(tool_result, ContinueResult):
                        self.user_input.stack(f"Result of {tool}\n{tool_result}")
            except (EOFError, KeyboardInterrupt):
                self.display.exit()
                break
        return tool_result

    def handle_user_message(self, context):
        user_message = self.user_input.read()
        if user_message:
            context.user_says(user_message)
        return user_message

    def handle_llm_answer(self, context):
        answer = self.llm(self.system_prompt, context.to_list())
        self.display.assistant_says(answer)
        context.assistant_says(answer)
        return answer
