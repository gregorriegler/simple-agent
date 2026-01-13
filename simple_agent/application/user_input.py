from typing import Protocol

from simple_agent.application.agent_id import AgentId


class UserInput(Protocol):
    async def read_async(self, agent_id: AgentId | None = None) -> str: ...

    def escape_requested(self) -> bool: ...

    def close(self) -> None: ...


class DummyUserInput(UserInput):
    async def read_async(self, agent_id: AgentId | None = None) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        pass
