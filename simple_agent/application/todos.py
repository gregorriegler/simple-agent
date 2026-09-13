from typing import Protocol

from .agent_id import AgentId


class Todos(Protocol):
    def read(self, agent_id: AgentId) -> str: ...

    def write(self, agent_id: AgentId, todos: str) -> None: ...
