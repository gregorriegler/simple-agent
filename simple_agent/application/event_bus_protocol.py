from typing import Protocol, Callable, Any, Type
from abc import abstractmethod
from .events import AgentEvent

EventHandler = Callable[[Any], None]
EventType = Type[AgentEvent]


class EventBus(Protocol):

    @abstractmethod
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        pass

    @abstractmethod
    def publish(self, event: AgentEvent) -> None:
        pass
