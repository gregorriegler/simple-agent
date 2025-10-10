from typing import Protocol, Callable, Any
from abc import abstractmethod

EventHandler = Callable[[Any], None]


class EventBus(Protocol):

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        pass

    @abstractmethod
    def publish(self, event_type: str, event_data: Any = None) -> None:
        pass
