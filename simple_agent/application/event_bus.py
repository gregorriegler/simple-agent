from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from .events import AgentEvent

T = TypeVar("T", bound=AgentEvent)


class EventBus(Protocol):
    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None: ...

    def publish(self, event: AgentEvent) -> None: ...


class SimpleEventBus(EventBus):
    def __init__(self):
        self._handlers: dict[type[AgentEvent], list[Any]] = {}

    def subscribe(self, event_type: type[T], handler: Callable[[T], None]) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: AgentEvent) -> None:
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event)
