from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

from simple_agent.application.agent_type import AgentType
from simple_agent.application.llm import Messages
from simple_agent.application.tool_library import ToolResult

if TYPE_CHECKING:
    from simple_agent.application.agent_factory import AgentFactory
    from simple_agent.application.agent_id import AgentId


class SubagentSpawner(Protocol):

    def __call__(self, agent_type: AgentType, task_description: str) -> ToolResult:
        ...


class BoundSubagentSpawner:
    """A spawner bound to a specific parent agent context."""

    def __init__(
        self,
        agent_factory: 'AgentFactory',
        parent_agent_id: 'AgentId',
        indent_level: int
    ):
        self._agent_factory = agent_factory
        self._parent_agent_id = parent_agent_id
        self._indent_level = indent_level

    def __call__(self, agent_type: AgentType, task_description: str) -> ToolResult:
        user_input = self._agent_factory.create_subagent_input()
        user_input.stack(task_description)

        subagent = self._agent_factory.create_subagent(
            agent_type,
            self._parent_agent_id,
            self._indent_level,
            user_input,
            Messages()
        )

        return subagent.start()
