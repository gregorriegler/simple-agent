from typing import Protocol

from .agent_id import AgentId


class UserInput(Protocol):
    async def read_async(self) -> str: ...

    def drain(self) -> list[str]:
        """Messages already waiting, without blocking for new ones."""
        return []

    def has_pending(self) -> bool:
        """Whether a message is waiting, without taking it."""
        return False

    def for_agent(self, agent_id: AgentId) -> "UserInput":
        """The channel this agent reads from; by default all agents share one."""
        return self

    def escape_requested(self) -> bool: ...

    def close(self) -> None: ...


class UserInputs(Protocol):
    """The user's side of every conversation: a keyboard channel per agent."""

    def for_agent(self, agent_id: AgentId) -> UserInput: ...

    def close(self) -> None: ...


class DummyUserInput(UserInput):
    async def read_async(self) -> str:
        return ""

    def drain(self) -> list[str]:
        return []

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        pass
