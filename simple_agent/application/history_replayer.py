import asyncio
import logging

from simple_agent.application.agent_id import AgentId
from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.event_bus import EventBus
from simple_agent.application.event_store import EventStore
from simple_agent.application.events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    ToolCalledEvent,
    ToolResultEvent,
)
from simple_agent.application.tool_library import ParsedTool

logger = logging.getLogger(__name__)


class HistoryReplayer:
    def __init__(self, event_bus: EventBus, event_store: EventStore):
        self._event_bus = event_bus
        self._event_store = event_store
        self._tool_syntax = EmojiBracketToolSyntax()

    async def replay_all_agents_async(
        self, starting_agent_id: AgentId
    ) -> list[AgentStartedEvent]:
        events = self._event_store.load_all_events()
        if not events:
            return []

        # Wait for UI to mount
        await asyncio.sleep(0.1)

        finished_agents = set()
        start_events = {}

        has_granular = any(
            isinstance(e, (AssistantSaidEvent, ToolCalledEvent)) for e in events
        )

        results_by_agent = {}
        if not has_granular:
            for e in events:
                if isinstance(e, ToolResultEvent):
                    results_by_agent.setdefault(e.agent_id, []).append(e)

        for i, event in enumerate(events):
            if isinstance(event, AgentFinishedEvent):
                finished_agents.add(event.agent_id)
            elif isinstance(event, AgentStartedEvent):
                start_events[event.agent_id] = event

            # In legacy mode, we don't publish raw ToolResultEvents alone
            if not has_granular and isinstance(event, ToolResultEvent):
                continue

            self._event_bus.publish(event)

            if not has_granular and isinstance(event, AssistantRespondedEvent):
                self._recover_legacy_assistant_response(
                    event, results_by_agent.get(event.agent_id, [])
                )

            # Cooperative multitasking
            if i % 10 == 0:
                await asyncio.sleep(0.01)

        return [
            e
            for aid, e in start_events.items()
            if aid not in finished_agents and aid != starting_agent_id
        ]

    def _recover_legacy_assistant_response(self, event, results):
        try:
            parsed = self._tool_syntax.parse(event.response)
            if parsed.message:
                self._event_bus.publish(
                    AssistantSaidEvent(agent_id=event.agent_id, message=parsed.message)
                )

            for i, raw_call in enumerate(parsed.tool_calls):
                tool = ParsedTool(raw_call, None)
                if results:
                    res_event = results.pop(0)
                    self._event_bus.publish(
                        ToolCalledEvent(
                            agent_id=event.agent_id,
                            call_id=res_event.call_id,
                            tool=tool,
                        )
                    )
                    self._event_bus.publish(res_event)
                else:
                    call_id = f"legacy_{event.agent_id.for_ui()}_{i}"
                    self._event_bus.publish(
                        ToolCalledEvent(
                            agent_id=event.agent_id, call_id=call_id, tool=tool
                        )
                    )
        except Exception:
            logger.warning(
                "Failed to recover legacy response for agent %s", event.agent_id
            )
