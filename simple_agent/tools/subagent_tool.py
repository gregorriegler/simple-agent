from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus

from ..application.agent_type import AgentType
from .base_tool import BaseTool


class SubagentTool(BaseTool):
    name = "subagent"
    description = "Creates a new subagent that will handle a specific task/todo and report back the result."
    arguments = ToolArguments(
        header=[
            ToolArgument(
                name="agenttype",
                type="string",
                required=True,
                description="Type of agent to create. {{AGENT_TYPES}}",
            ),
            ToolArgument(
                name="task_description",
                type="string",
                required=True,
                description="Detailed description of the task for the subagent to perform",
            ),
            ToolArgument(
                name="--async",
                type="bool",
                required=False,
                description="Run the subagent asynchronously, returning immediately without waiting for it to finish.",
            ),
        ]
    )
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
        self._agent_types = agent_types

    async def execute(self, raw_call):
        named = raw_call.named_arguments
        agent_type_str = named.get("agenttype", "")
        task_description = str(named.get("task_description", "")).strip()
        is_async = raw_call.flag("--async")

        if not agent_type_str or not task_description:
            return SingleToolResult(
                "STDERR: subagent: missing agenttype or task description",
                status=ToolResultStatus.FAILURE,
            )

        try:
            result = await self._spawn_subagent(
                AgentType(agent_type_str), task_description, is_async
            )
            status = (
                ToolResultStatus.SUCCESS if result.success else ToolResultStatus.FAILURE
            )
            return SingleToolResult(str(result), status=status)
        except Exception as e:
            return SingleToolResult(
                f"STDERR: subagent error: {str(e)}", status=ToolResultStatus.FAILURE
            )

    def get_template_variables(self) -> dict:
        if not self._agent_types:  # Empty AgentTypes
            return {}
        types_str = ", ".join(f"'{t}'" for t in self._agent_types)
        return {"AGENT_TYPES": f"Available types: {types_str}"}
