from agent import Display
from chat import Chat

from .base_tool import BaseTool


class SubagentTool(BaseTool):
    name = 'subagent'
    description = "Create a subagent to handle a specific task using the same agent architecture"
    arguments = [
        {
            "name": "task_description",
            "type": "string",
            "required": True,
            "description": "Detailed description of the task for the subagent to perform"
        }
    ]
    examples = [
        "🛠️ subagent Write a Python function to calculate fibonacci numbers",
        "🛠️ subagent Create a simple HTML page with a form"
    ]

    def __init__(self, runcommand, message_claude, indent_level=0):
        super().__init__()
        self.runcommand = runcommand
        self.message_claude = message_claude
        self.indent_level = indent_level

    def execute(self, args):
        if not args or not args.strip():
            return 'STDERR: subagent: missing task description'

        try:
            # Import Agent and SystemPromptGenerator here to avoid circular dependency
            from agent import Agent
            from system_prompt_generator import SystemPromptGenerator

            system_prompt = SystemPromptGenerator().generate_system_prompt()
            subagent_display = SubagentDisplay(self.indent_level + 1)

            # Create a new ToolLibrary instance for the subagent to avoid recursion
            from tools.tool_library import ToolLibrary
            subagent_tools = ToolLibrary(self.message_claude, self.indent_level + 1)
            subagent = Agent(system_prompt, self.message_claude, subagent_display, subagent_tools)

            subagent_chat = Chat()
            subagent_chat.user_says(args.strip())
            result = subagent.start(subagent_chat)
            return f"{result}\n"

        except Exception as e:
            return f'STDERR: subagent error: {str(e)}'


class SubagentDisplay(Display):

    def __init__(self, indent_level=1):
        super().__init__()
        self.indent_level = indent_level
        self.base_indent = "       " * (indent_level + 1)  # 7 spaces per level
        self.agent_prefix = "       " * indent_level + "Subagent: "

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines:
            print(f"\n{self.agent_prefix}{lines[0]}")
            for line in lines[1:]:
                print(f"{self.base_indent}{line}")

    def tool_result(self, result):
        indented_result = self._indent_lines(result, self.base_indent)
        print(f"\n{indented_result}")

    def input(self):
        prompt = "       " * self.indent_level + "Press Enter to continue or type a message to add: "
        return input(f"\n{prompt}")

    def tool_about_to_execute(self, parsed_tool):
        indented_tool = self._indent_lines(str(parsed_tool), "       " * self.indent_level)
        print(f"\n{indented_tool}")

    def exit(self):
        pass

    def _indent_lines(self, text, prefix="           "):
        lines = str(text).split('\n')
        return '\n'.join(f"{prefix}{line}" for line in lines)
