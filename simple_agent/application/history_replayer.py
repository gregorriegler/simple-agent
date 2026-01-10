from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import EventBus
from simple_agent.application.event_store import EventStore
from simple_agent.application.events import (
    AssistantRespondedEvent,
    AssistantSaidEvent,
)


class HistoryReplayer:
    def __init__(self, event_bus: EventBus, event_store: EventStore):
        self._event_bus = event_bus
        self._event_store = event_store

    def replay_all_agents(self, starting_agent_id: AgentId) -> None:
        events = self._event_store.load_all_events()
        for event in events:
            if isinstance(event, AssistantRespondedEvent):
                self._event_bus.publish(
                    AssistantSaidEvent(agent_id=event.agent_id, message=event.response)
                )
            self._event_bus.publish(event)
