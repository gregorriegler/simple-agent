from typing import Protocol, Callable, Type, TypeVar
from abc import abstractmethod
from .events import AgentEvent

T = TypeVar('T', bound=AgentEvent)

EventHandler = Callable[[AgentEvent], None]
EventType = Type[AgentEvent]


class EventBus(Protocol):

    @abstractmethod
    def subscribe(self, event_type: Type[T], handler: Callable[[T], None]) -> None:
        pass

    @abstractmethod
    def unsubscribe(self, event_type: Type[T], handler: Callable[[T], None]) -> None:
        pass

    @abstractmethod
    def publish(self, event: AgentEvent) -> None:
        pass
