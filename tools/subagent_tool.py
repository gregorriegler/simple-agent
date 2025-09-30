from application.llm import Messages
from application.input import Input
from infrastructure.console_display import ConsoleDisplay
from infrastructure.console_escape_detector import ConsoleEscapeDetector

from .base_tool import BaseTool


class NoOpSessionStorage:

    def load(self) -> Messages:
        return Messages()

    def save(self, messages: Messages):
        return None


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

    def __init__(self, runcommand, llm, indent_level=0, print_fn=print):
        super().__init__()
        self.runcommand = runcommand
        self.llm = llm
        self.indent_level = indent_level
        self.print_fn = print_fn
        self.subagent_display = SubagentDisplay(self.indent_level + 1, self.print_fn)

    def execute(self, args):
        if not args or not args.strip():
            return 'STDERR: subagent: missing task description'

        try:
            from application.agent import Agent
            from system_prompt_generator import SystemPromptGenerator

            system_prompt = SystemPromptGenerator().generate_system_prompt()

            from tools.tool_library import ToolLibrary
            subagent_tools = ToolLibrary(self.llm, self.indent_level + 1, self.print_fn)
            subagent_session_storage = NoOpSessionStorage()
            esc_detector = ConsoleEscapeDetector()
            user_input = Input(self.subagent_display, esc_detector)
            user_input.stack(args)
            subagent = Agent(
                self.llm,
                system_prompt,
                user_input,
                subagent_tools,
                self.subagent_display,
                subagent_session_storage
            )

            subagent_messages = Messages()
            result = subagent.start(subagent_messages)
            return result

        except Exception as e:
            return f'STDERR: subagent error: {str(e)}'


class SubagentDisplay(ConsoleDisplay):

    def __init__(self, indent_level=1, print_fn=print):
        super().__init__(indent_level, print_fn, "Subagent")

    def exit(self):
        pass
