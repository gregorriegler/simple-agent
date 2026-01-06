from typing import Dict, List, Type, Callable, TypeVar, Any, Protocol
from .events import AgentEvent

T = TypeVar("T", bound=AgentEvent)


class EventBus(Protocol):
    def subscribe(self, event_type: Type[T], handler: Callable[[T], None]) -> None: ...

    def publish(self, event: AgentEvent) -> None: ...


class SimpleEventBus(EventBus):
    def __init__(self):
        self._handlers: Dict[Type[AgentEvent], List[Any]] = {}

    def subscribe(self, event_type: Type[T], handler: Callable[[T], None]) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: AgentEvent) -> None:
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event)
