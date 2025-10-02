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
        try:
            tool_result: ToolResult = ContinueResult()
            for _ in range(rounds):
                prompt = self.user_prompts(context)
                if not prompt:
                    self.display.exit()
                    return tool_result

                llm_answer = self.llm_answers(context)

                if self.user_interrupts():
                    continue

                tool_result = self.call_tool(llm_answer)
            return tool_result
        except (EOFError, KeyboardInterrupt):
            self.display.exit()
            return ContinueResult()

    def user_prompts(self, context):
        prompt = self.user_input.read()
        if prompt:
            context.user_says(prompt)
        return prompt

    def llm_answers(self, context):
        answer = self.llm(self.system_prompt, context.to_list())
        self.display.assistant_says(answer)
        context.assistant_says(answer)
        return answer

    def user_interrupts(self):
        return self.user_input.escape_requested()

    def call_tool(self, llm_answer):
        tool = self.tools.parse_tool(llm_answer)
        if tool:
            tool_result = self.tools.execute_parsed_tool(tool)
            self.display.tool_result(str(tool_result))
            if isinstance(tool_result, ContinueResult):
                self.user_input.stack(f"Result of {tool}\n{tool_result}")
            return tool_result
        return ContinueResult()
