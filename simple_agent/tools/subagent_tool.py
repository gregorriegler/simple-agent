from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import ContinueResult, ToolArgument, ToolArguments
from .base_tool import BaseTool
from ..application.agent_type import AgentType


class SubagentTool(BaseTool):
    name = 'subagent'
    description = "Creates a new subagent that will handle a specific task/todo and report back the result."
    arguments = ToolArguments([
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
    ])
    examples = [
        {
            "agenttype": "default",
            "task_description": "Write a Python function to calculate fibonacci numbers",
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

    def execute(self, raw_call):
        args = raw_call.arguments
        if not args or not args.strip():
            return ContinueResult('STDERR: subagent: missing arguments', success=False)

        parts = args.strip().split(None, 1)

        if len(parts) < 2:
            return ContinueResult('STDERR: subagent: missing agenttype or task description', success=False)

        agent_type_str = parts[0]
        task_description = parts[1]

        try:
            result = self._spawn_subagent(
                AgentType(agent_type_str),
                task_description
            )
            return ContinueResult(str(result), success=result.success)
        except Exception as e:
            return ContinueResult(f'STDERR: subagent error: {str(e)}', success=False)

    def get_template_variables(self) -> dict:
        if not self._agent_types:  # Empty AgentTypes
            return {}
        types_str = ', '.join(f"'{t}'" for t in self._agent_types)
        return {'AGENT_TYPES': f"Available types: {types_str}"}
