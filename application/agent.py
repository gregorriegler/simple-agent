from .llm import LLM
from .session_storage import SessionStorage
from .tool_result import ToolResult, ContinueResult, CompleteResult


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
            remaining_rounds = rounds
            while remaining_rounds > 0:
                prompt = self.user_prompts(context)
                if not prompt:
                    self.display.exit()
                    return tool_result

                tool_result, used_rounds = self.run_tool_loop(context, remaining_rounds)
                remaining_rounds -= used_rounds
            return tool_result
        except (EOFError, KeyboardInterrupt):
            self.display.exit()
            return ContinueResult()

    def run_tool_loop(self, context, remaining_rounds):
        tool_result: ToolResult = ContinueResult()
        rounds_used = 0
        while isinstance(tool_result, ContinueResult) and rounds_used < remaining_rounds:
            rounds_used += 1
            llm_answer = self.llm_answers(context)
            tool = self.tools.parse_tool(llm_answer)
            if not tool or self.user_interrupts():
                return ContinueResult(), rounds_used

            tool_result = self.execute_tool(tool)
            if isinstance(tool_result, CompleteResult):
                return tool_result, rounds_used

            context.user_says(f"Result of {tool}\n{tool_result}")

        return tool_result, rounds_used

    def execute_tool(self, tool):
        tool_result = self.tools.execute_parsed_tool(tool)
        self.display.tool_result(str(tool_result))
        return tool_result

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
