from typing import Protocol

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import ToolLibrary


class Inbox(Protocol):
    """
    Where messages for the agent that owns the tools arrive: a stacked
    message reaches the agent as if the user had sent it.
    """

    def stack(self, message: str) -> None: ...

    async def wait_for_message(self, timeout: float) -> bool: ...


class NoInbox:
    def stack(self, message: str) -> None:
        pass

    async def wait_for_message(self, timeout: float) -> bool:
        return False


class ToolContext:
    def __init__(
        self, tool_keys: list[str], agent_id: AgentId, inbox: Inbox | None = None
    ):
        self.tool_keys = tool_keys
        self.agent_id = agent_id
        self.inbox: Inbox = inbox or NoInbox()


class ToolLibraryFactory(Protocol):
    def create(
        self,
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        agent_types: AgentTypes,
    ) -> ToolLibrary: ...
