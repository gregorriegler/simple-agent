from typing import Protocol, Callable, Any
from abc import abstractmethod
from .events import EventType

EventHandler = Callable[[Any], None]


class EventBus(Protocol):

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        pass

    @abstractmethod
    def publish(self, event_type: EventType, event_data: Any = None) -> None:
        pass
