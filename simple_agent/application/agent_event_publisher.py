from .agent_id import AgentId
from .event_bus import EventBus
from .events import AgentEvent


class AgentEventPublisher:
    def __init__(self, agent_id: AgentId, event_bus: EventBus):
        self._agent_id = agent_id
        self._event_bus = event_bus

    def publish(self, event: AgentEvent) -> None:
        if event.agent_id is None:
            event.agent_id = self._agent_id
        self._event_bus.publish(event)
