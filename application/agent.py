from .llm import LLM
from .session_storage import SessionStorage
from .agent_result import AgentResult, ContinueResult


class Agent:
    def __init__(self, llm: LLM, system_prompt, user_input, tools, display, session_storage: SessionStorage):
        self.llm: LLM = llm
        self.system_prompt = system_prompt
        self.user_input = user_input
        self.display = display
        self.tools = tools
        self.session_storage = session_storage

    def start(self, context, rounds=999999):
        result: AgentResult = ContinueResult("")
        for _ in range(rounds):
            try:
                user_message = self.user_input.read()
                if user_message:
                    context.user_says(user_message)
                else:
                    self.display.exit()
                    return result
                answer = self.llm(self.system_prompt, context.to_list())
                self.display.assistant_says(answer)
                context.assistant_says(answer)
                if self.user_input.escape_requested():
                    user_message = self.user_input.read()
                    if user_message:
                        context.user_says(user_message)
                        break
                tool = self.tools.parse_tool(answer)
                if tool:
                    execution_result = self.tools.execute_parsed_tool(tool)
                    self.display.tool_result(execution_result.feedback)
                    if isinstance(execution_result, ContinueResult):
                        self.user_input.stack(f"Result of {tool}\n{execution_result}")
                    result = execution_result
            except (EOFError, KeyboardInterrupt):
                self.display.exit()
                break
        return result
