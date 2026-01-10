from typing import Protocol

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import AgentEvent


class EventStore(Protocol):
    def persist(self, event: AgentEvent) -> None: ...

    def load_events(self, agent_id: AgentId | None = None) -> list[AgentEvent]: ...

    def load_all_events(self) -> list[AgentEvent]: ...
