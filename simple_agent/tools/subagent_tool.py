from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus

from ..application.agent_type import AgentType
from .base_tool import BaseTool


def _arguments(agenttype_description: str) -> ToolArguments:
    return ToolArguments(
        header=[
            ToolArgument(
                name="agenttype",
                type="string",
                required=True,
                description=agenttype_description,
            ),
            ToolArgument(
                name="task_description",
                type="string",
                required=True,
                description="Detailed description of the task for the subagent to perform",
            ),
            ToolArgument(
                name="--background",
                type="bool",
                required=False,
                description="Run the subagent in the background: return immediately, and receive its summary as a message once it completes.",
            ),
        ]
    )


def _task_and_result(task_description: str, result: str) -> str:
    return f"## Task\n\n{task_description}\n\n## Result\n\n{result}"


class SubagentTool(BaseTool):
    name = "subagent"
    description = "Creates a new subagent that will handle a specific task/todo and report back the result."
    arguments = _arguments("Type of agent to create.")
    examples = [
        {
            "reasoning": "Let's say you want to delegate a coding task to a subagent. Send the following:",
            "agenttype": "default",
            "task_description": "Write a Python function to calculate fibonacci numbers",
            "result": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
        },
        {
            "agenttype": "default",
            "task_description": "Create a simple HTML page with a form",
        },
    ]

    def __init__(self, spawn_subagent: SubagentSpawner, agent_types: AgentTypes):
        super().__init__()
        self._spawn_subagent = spawn_subagent
        self.arguments = _arguments(self._agenttype_description(agent_types))

    @staticmethod
    def _agenttype_description(agent_types: AgentTypes) -> str:
        if not agent_types:
            return "Type of agent to create."
        types_str = ", ".join(f"'{t}'" for t in agent_types)
        return f"Type of agent to create. Available types: {types_str}"

    async def execute(self, call):
        named = call.named_arguments
        agent_type_str = named.get("agenttype", "")
        task_description = str(named.get("task_description", "")).strip()
        background = named.get("--background", False)

        if not agent_type_str or not task_description:
            return SingleToolResult(
                "STDERR: subagent: missing agenttype or task description",
                status=ToolResultStatus.FAILURE,
            )

        try:
            result = await self._spawn_subagent(
                AgentType(agent_type_str), task_description, background
            )
            status = (
                ToolResultStatus.SUCCESS if result.success else ToolResultStatus.FAILURE
            )
            return SingleToolResult(
                str(result),
                status=status,
                display_body=_task_and_result(task_description, str(result)),
                display_language="markdown",
            )
        except Exception as e:
            return SingleToolResult(
                f"STDERR: subagent error: {str(e)}", status=ToolResultStatus.FAILURE
            )
