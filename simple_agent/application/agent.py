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

    def start(self, context):
        try:
            tool_result: ToolResult = ContinueResult()

            while self.user_prompts(context):
                tool_result = self.run_tool_loop(context)

            self.display.exit()
            return tool_result
        except (EOFError, KeyboardInterrupt):
            self.display.exit()
            return ContinueResult()

    def run_tool_loop(self, context):
        tool_result: ToolResult = ContinueResult()

        try:
            while isinstance(tool_result, ContinueResult):
                llm_answer = self.llm_answers(context)
                tool = self.tools.parse_tool(llm_answer)
                if not tool or self.user_input.escape_requested():
                    break
                tool_result = self.execute_tool(tool, context)
        except KeyboardInterrupt:
            pass

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

    def execute_tool(self, tool, context):
        tool_result = self.tools.execute_parsed_tool(tool)
        self.display.tool_result(str(tool_result))
        if isinstance(tool_result, ContinueResult):
            context.user_says(f"Result of {tool}\n{tool_result}")
        return tool_result
