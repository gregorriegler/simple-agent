from agent import Display
from chat import Chat
from console_display import ConsoleDisplay

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

    def __init__(self, runcommand, message_claude, indent_level=0, print_fn=print):
        super().__init__()
        self.runcommand = runcommand
        self.message_claude = message_claude
        self.indent_level = indent_level
        self.print_fn = print_fn

    def execute(self, args):
        if not args or not args.strip():
            return 'STDERR: subagent: missing task description'

        try:
            # Import Agent and SystemPromptGenerator here to avoid circular dependency
            from agent import Agent
            from system_prompt_generator import SystemPromptGenerator

            system_prompt = SystemPromptGenerator().generate_system_prompt()
            subagent_display = SubagentDisplay(self.indent_level + 1, self.print_fn)

            # Create a new ToolLibrary instance for the subagent to avoid recursion
            from tools.tool_library import ToolLibrary
            subagent_tools = ToolLibrary(self.message_claude, self.indent_level + 1, self.print_fn)
            subagent = Agent(system_prompt, self.message_claude, subagent_display, subagent_tools)

            subagent_chat = Chat()
            subagent_chat.user_says(args.strip())
            result = subagent.start(subagent_chat)
            return result

        except Exception as e:
            return f'STDERR: subagent error: {str(e)}'


class SubagentDisplay(ConsoleDisplay):

    def __init__(self, indent_level=1, print_fn=print):
        super().__init__(indent_level, print_fn, "Subagent")

    def exit(self):
        pass
