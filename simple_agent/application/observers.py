from collections.abc import Callable
from typing import Protocol

from .agent_id import AgentId
from .change_reporter import ChangeReporter
from .event_bus import EventBus
from .events import (
    AgentFinishedEvent,
    CheckpointReachedEvent,
    SessionClearedEvent,
    ToolCalledEvent,
)
from .input import Input
from .intent import Intent

SUGGEST_TOOL = "suggest"


class Observer(Protocol):
    agent_id: AgentId

    def observe(self, packet: str) -> None: ...

    def close(self) -> None: ...


class Observers:
    def __init__(
        self,
        event_bus: EventBus,
        agent_id: AgentId,
        names: list[str],
        change_reporter: ChangeReporter,
        create_observer: Callable[[str], Observer],
        agent_input: Input,
        intent: Intent,
    ):
        self._agent_id = agent_id
        self._names = names
        self._change_reporter = change_reporter
        self._create_observer = create_observer
        self._agent_input = agent_input
        self._intent = intent
        self._observers: dict[str, Observer] = {}
        event_bus.subscribe(CheckpointReachedEvent, self._observe)
        event_bus.subscribe(AgentFinishedEvent, self._close)
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
                self._agent_input.stack(
                    f"Suggestion from the {name} observer:\n{event.call.body.strip()}"
                )

    def _close(self, event: AgentFinishedEvent | SessionClearedEvent) -> None:
        if event.agent_id != self._agent_id:
            return
        for observer in self._observers.values():
            observer.close()
        self._observers.clear()

    def _packet(self, diff: str) -> str:
        intent = self._intent.read()
        if not intent:
            return diff
        return f"Intent: {intent}\n\n{diff}"

    def _observer(self, name: str) -> Observer:
        if name not in self._observers:
            self._observers[name] = self._create_observer(name)
        return self._observers[name]
