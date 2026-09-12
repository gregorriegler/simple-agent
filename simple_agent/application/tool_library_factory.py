from collections.abc import Callable
from typing import Protocol

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import ToolLibrary

Report = Callable[[str], None]
"""Brings a message to the agent that owns the tools, as if the user had sent it."""


def _ignore(message: str) -> None:
    pass


class ToolContext:
    def __init__(
        self, tool_keys: list[str], agent_id: AgentId, report: Report = _ignore
    ):
        self.tool_keys = tool_keys
        self.agent_id = agent_id
        self.report = report


class ToolLibraryFactory(Protocol):
    def create(
        self,
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        agent_types: AgentTypes,
    ) -> ToolLibrary: ...
