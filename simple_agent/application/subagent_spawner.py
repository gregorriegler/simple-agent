from typing import Awaitable, Protocol

from simple_agent.application.agent_type import AgentType
from simple_agent.application.tool_results import ToolResult


class SubagentSpawner(Protocol):

    def __call__(self, agent_type: AgentType, task_description: str) -> Awaitable[ToolResult]:
        ...
