from typing import Protocol

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import ToolLibrary


class ToolContext:

    def __init__(self, tool_keys: list[str], agent_id: AgentId):
        self.tool_keys = tool_keys
        self.agent_id = agent_id


class ToolLibraryFactory(Protocol):
    def create(
        self,
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        agent_types: AgentTypes
    ) -> ToolLibrary:
        ...
