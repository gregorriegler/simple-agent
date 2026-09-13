from typing import Protocol

from .agent_id import AgentId
from .agent_type import AgentType
from .change_reporter import ChangeReporter
from .event_bus import EventBus
from .events import (
    AgentFinishedEvent,
    CheckpointReachedEvent,
    SessionClearedEvent,
    ToolCalledEvent,
)
from .inbox import Inbox
from .intent import Intents

SUGGEST_TOOL = "suggest"


class Observer(Protocol):
    agent_id: AgentId

    def observe(self, packet: str) -> None: ...

    def close(self) -> None: ...


class ObserverSpawner(Protocol):
    def __call__(self, name: str) -> Observer: ...

    def create_from_history(
        self, agent_id: AgentId, agent_type: AgentType
    ) -> Observer: ...


class Observers:
    def __init__(
        self,
        event_bus: EventBus,
        agent_id: AgentId,
        names: list[str],
        change_reporter: ChangeReporter,
        create_observer: ObserverSpawner,
        inbox: Inbox,
        intents: Intents,
    ):
        self._agent_id = agent_id
        self._names = names
        self._change_reporter = change_reporter
        self._create_observer = create_observer
        self._inbox = inbox
        self._intents = intents
        self._observers: dict[str, Observer] = {}
        self._event_bus = event_bus
        event_bus.subscribe(CheckpointReachedEvent, self._observe)
        event_bus.subscribe(AgentFinishedEvent, self._finish)
        event_bus.subscribe(SessionClearedEvent, self._close)
        event_bus.subscribe(ToolCalledEvent, self._deliver)

    def _observe(self, event: CheckpointReachedEvent) -> None:
        if event.agent_id != self._agent_id:
            return
        diff = self._change_reporter.diff()
        if not diff:
            return
        packet = self._packet(diff)
        for name in self._names:
            self._observer(name).observe(packet)

    def _deliver(self, event: ToolCalledEvent) -> None:
        if not event.call or event.call.name != SUGGEST_TOOL:
            return
        for name, observer in self._observers.items():
            if observer.agent_id == event.agent_id:
                self._inbox.put(
                    f"💡 Suggestion from the {name} observer:\n{str(event.call.named_arguments.get('suggestion', '')).strip()}"
                )

    def _close(self, event: AgentFinishedEvent | SessionClearedEvent) -> None:
        if event.agent_id != self._agent_id:
            return
        for observer in self._observers.values():
            observer.close()
        self._observers.clear()

    def _finish(self, event: AgentFinishedEvent) -> None:
        if event.agent_id != self._agent_id:
            return
        self._close(event)
        self._event_bus.unsubscribe(CheckpointReachedEvent, self._observe)
        self._event_bus.unsubscribe(AgentFinishedEvent, self._finish)
        self._event_bus.unsubscribe(SessionClearedEvent, self._close)
        self._event_bus.unsubscribe(ToolCalledEvent, self._deliver)

    def _packet(self, diff: str) -> str:
        intent = self._intents.read(self._agent_id)
        if not intent:
            return diff
        return f"Intent: {intent}\n\n{diff}"

    def resume(self, agent_id: AgentId, agent_type: AgentType) -> bool:
        name = agent_type.raw
        if name not in self._names or name in self._observers:
            return False
        self._observers[name] = self._create_observer.create_from_history(
            agent_id, agent_type
        )
        return True

    def _observer(self, name: str) -> Observer:
        if name not in self._observers:
            self._observers[name] = self._create_observer(name)
        return self._observers[name]
