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
        "/subagent Write a Python function to calculate fibonacci numbers",
        "/subagent Create a simple HTML page with a form"
    ]

    def __init__(self, runcommand, message_claude):
        super().__init__()
        self.runcommand = runcommand
        self.message_claude = message_claude

    def execute(self, args):
        if not args or not args.strip():
            return 'STDERR: subagent: missing task description'

        try:
            # Import Agent and SystemPromptGenerator here to avoid circular dependency
            from agent import Agent
            from system_prompt_generator import SystemPromptGenerator

            system_prompt = SystemPromptGenerator().generate_system_prompt()
            subagent_display = SubagentDisplay()

            # Create a new ToolLibrary instance for the subagent to avoid recursion
            from tools.tool_library import ToolLibrary
            subagent_tools = ToolLibrary(self.message_claude)
            subagent = Agent(system_prompt, self.message_claude, subagent_display, subagent_tools)

            subagent_chat = Chat()
            subagent_chat.user_says(args.strip())
            result = subagent.start(subagent_chat)
            return f"{result}"

        except Exception as e:
            return f'STDERR: subagent error: {str(e)}'


class SubagentDisplay(Display):

    def __init__(self):
        super().__init__()

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines:
            print(f"\n    Subagent: {lines[0]}")
            for line in lines[1:]:
                print(f"              {line}")

    def tool_result(self, result):
        indented_result = self._indent_lines(result)
        print(indented_result)

    def input(self):
        return input("\n    Press Enter to continue or type a message to add: ")

    def tool_about_to_execute(self, parsed_tool):
        indented_tool = self._indent_lines(parsed_tool, "\n    ")
        print(indented_tool)

    def exit(self):
        print("    Subagent completed.")

    def _indent_lines(self, text, prefix="    "):
        lines = str(text).split('\n')
        return '\n'.join(f"{prefix}{line}" for line in lines)
