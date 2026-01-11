from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import EventBus
from simple_agent.application.event_store import EventStore
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
)


class HistoryReplayer:
    def __init__(self, event_bus: EventBus, event_store: EventStore):
        self._event_bus = event_bus
        self._event_store = event_store

    def replay_all_agents(self, starting_agent_id: AgentId) -> list[AgentStartedEvent]:
        """Replay events and return list of unfinished subagent start events that need to be re-spawned."""
        events = self._event_store.load_all_events()
        finished_agents = set()
        start_events = {}

        for event in events:
            if isinstance(event, AgentFinishedEvent):
                finished_agents.add(event.agent_id)
            elif isinstance(event, AgentStartedEvent):
                start_events[event.agent_id] = event

        for event in events:
            if (
                isinstance(event, AgentStartedEvent)
                and event.agent_id in finished_agents
                and event.agent_id != starting_agent_id
            ):
                continue
            if isinstance(event, AssistantRespondedEvent):
                self._event_bus.publish(
                    AssistantSaidEvent(agent_id=event.agent_id, message=event.response)
                )
            self._event_bus.publish(event)

        unfinished_subagents = [
            event
            for agent_id, event in start_events.items()
            if agent_id not in finished_agents and agent_id != starting_agent_id
        ]
        return unfinished_subagents
