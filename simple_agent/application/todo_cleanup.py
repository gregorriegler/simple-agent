from typing import Protocol

from simple_agent.application.agent_id import AgentId


class TodoCleanup(Protocol):
    def cleanup_all_todos(self) -> None: ...

    def cleanup_todos_for_agent(self, agent_id: AgentId) -> None: ...
