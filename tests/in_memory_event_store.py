from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import AgentEvent


class InMemoryEventStore:
    def __init__(self, *events: AgentEvent):
        self._events: list[AgentEvent] = list(events)

    def persist(self, event: AgentEvent) -> None:
        self._events.append(event)

    def load_events(self, agent_id: AgentId | None = None) -> list[AgentEvent]:
        if agent_id is None:
            return list(self._events)
        return [event for event in self._events if event.agent_id == agent_id]

    def load_all_events(self) -> list[AgentEvent]:
        return list(self._events)
