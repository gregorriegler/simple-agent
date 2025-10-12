from typing import Protocol

from simple_agent.application.agent import Agent
from simple_agent.application.input import Input
from simple_agent.application.tool_library import ContinueResult
from simple_agent.infrastructure.display_event_handler import DisplayEventHandler
from .base_tool import BaseTool


class CreateAgent(Protocol):
    def __call__(
        self,
        agent_id: str,
        user_input: Input,
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
        create_agent: CreateAgent,
        create_display,
        indent_level: int,
        parent_agent_id: str,
        display_event_handler,
        user_input: Input
    ):
        super().__init__()
        self.create_agent = create_agent
        self.create_display = create_display
        self.indent_level = indent_level
        self.parent_agent_id = parent_agent_id
        self.display_event_handler = display_event_handler
        self.user_input = user_input

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult('STDERR: subagent: missing task description')
        try:
            self.user_input.stack(args)
            agent_id = f"{self.parent_agent_id}/Subagent{self.indent_level + 1}"
            subagent = self.create_agent(
                agent_id,
                self.user_input,
                self.display_event_handler
            )
            if self.display_event_handler:
                subagent_display = self.create_display(subagent.agent_id)
                self.display_event_handler.register_display(subagent.agent_id, subagent_display)
            result = subagent.start()
            if self.display_event_handler:
                del self.display_event_handler.displays[subagent.agent_id]
            return ContinueResult(str(result))
        except Exception as e:
            return ContinueResult(f'STDERR: subagent error: {str(e)}')
