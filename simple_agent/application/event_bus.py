from typing import Callable, Any, Dict, List
from .event_bus_protocol import EventBus


class SimpleEventBus(EventBus):

    def __init__(self):
        self._handlers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
            except ValueError:
                pass

    def publish(self, event_type: str, event_data: Any = None) -> None:
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event_data)
