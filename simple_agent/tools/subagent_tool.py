from typing import Protocol

from simple_agent.application.display import Display
from simple_agent.application.io import IO
from simple_agent.application.input import Input
from simple_agent.application.llm import Messages
from simple_agent.application.tool_result import ContinueResult, ToolResult
from simple_agent.infrastructure.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.infrastructure.display_event_handler import DisplayEventHandler
from .base_tool import BaseTool


class Agent(Protocol):
    def start(self, context: Messages) -> ToolResult:
        ...


class AgentBuilder(Protocol):
    def __call__(
        self,
        agent_id: str,
        user_input: Input,
        display: Display,
        display_event_handler: DisplayEventHandler
    ) -> Agent:
        ...


class SubagentTool(BaseTool):
    name = 'subagent'
    description = "Creates a new subagent that will handle a specific task/todo and report back the result."
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

    def __init__(
        self,
        agent_builder: AgentBuilder,
        display: Display,
        indent_level=0
        , io: IO | None = None,
        display_handler: DisplayEventHandler | None = None,
        parent_agent_id: str = "Agent"
    ):
        super().__init__()
        self.agent_builder = agent_builder
        self.indent_level = indent_level
        self.io = io or StdIO()
        self.display_event_handler = display_handler
        self.parent_agent_id = parent_agent_id
        self.subagent_display = display
        self.subagent_counter = 0

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult('STDERR: subagent: missing task description')
        try:
            user_input_port = ConsoleUserInput(self.indent_level + 1, self.io, allow_escape=False)
            user_input = Input(user_input_port)
            user_input.stack(args)
            self.subagent_counter += 1
            subagent_id = f"{self.parent_agent_id}/Subagent{self.subagent_counter}"
            subagent = self.agent_builder(
                subagent_id,
                user_input,
                self.subagent_display,
                self.display_event_handler
            )
            subagent_messages = Messages()
            result = subagent.start(subagent_messages)
            del self.display_event_handler.displays[subagent_id]
            return ContinueResult(str(result))
        except Exception as e:
            return ContinueResult(f'STDERR: subagent error: {str(e)}')
