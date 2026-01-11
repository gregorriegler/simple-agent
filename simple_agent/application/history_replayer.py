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

    def replay_all_agents(self, starting_agent_id: AgentId) -> None:
        events = self._event_store.load_all_events()
        finished_agents = set()
        agents_with_start_event = set()

        for event in events:
            if isinstance(event, AgentFinishedEvent):
                finished_agents.add(event.agent_id)
            elif isinstance(event, AgentStartedEvent):
                agents_with_start_event.add(event.agent_id)

        # # Synthesize AgentStartedEvent for starting agent if not present in history
        # # This ensures the UI creates the tab before replaying messages
        # if starting_agent_id not in agents_with_start_event:
        #     self._event_bus.publish(
        #         AgentStartedEvent(
        #             agent_id=starting_agent_id,
        #             agent_name=str(starting_agent_id),
        #             model="",
        #         )
        #     )

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
