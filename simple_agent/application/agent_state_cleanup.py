from typing import Protocol

from simple_agent.application.agent_id import AgentId


class AgentStateCleanup(Protocol):
    def cleanup_all(self) -> None: ...

    def cleanup_for_agent(self, agent_id: AgentId) -> None: ...
