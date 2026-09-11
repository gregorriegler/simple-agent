import asyncio

from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import EventBus
from simple_agent.application.event_store import EventStore
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    SessionClearedEvent,
    ToolCalledEvent,
    ToolResultEvent,
)


class HistoryReplayer:
    def __init__(self, event_bus: EventBus, event_store: EventStore):
        self._event_bus = event_bus
        self._event_store = event_store

    async def replay_all_agents_async(
        self, starting_agent_id: AgentId
    ) -> list[AgentStartedEvent]:
        events = _since_last_clear(self._event_store.load_all_events())
        if not events:
            return []

        # Wait for UI to mount
        await asyncio.sleep(0.1)

        finished_agents = set()
        start_events = {}

        has_granular = any(
            isinstance(e, (AssistantSaidEvent, ToolCalledEvent)) for e in events
        )

        for i, event in enumerate(events):
            if isinstance(event, AgentFinishedEvent):
                finished_agents.add(event.agent_id)
            elif isinstance(event, AgentStartedEvent):
                start_events[event.agent_id] = event

            if not has_granular and isinstance(event, ToolResultEvent):
                continue

            self._event_bus.publish(event)

            if not has_granular and isinstance(event, AssistantRespondedEvent):
                self._event_bus.publish(
                    AssistantSaidEvent(agent_id=event.agent_id, message=event.response)
                )

            # Cooperative multitasking
            if i % 10 == 0:
                await asyncio.sleep(0.01)

        return [
            e
            for aid, e in start_events.items()
            if aid not in finished_agents and aid != starting_agent_id
        ]


def _since_last_clear(events: list) -> list:
    """Clearing starts a fresh session, so anything before it is not ours to replay.

    New sessions rotate their event log on clear; older logs kept everything.
    """
    for i in range(len(events) - 1, -1, -1):
        if isinstance(events[i], SessionClearedEvent):
            return events[i + 1 :]
    return events
