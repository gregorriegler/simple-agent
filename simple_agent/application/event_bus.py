from typing import Any, Dict, List
from .event_bus_protocol import EventBus, EventHandler
from .events import EventType


class SimpleEventBus(EventBus):

    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
            except ValueError:
                pass

    def publish(self, event_type: EventType, event_data: Any = None) -> None:
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event_data)
