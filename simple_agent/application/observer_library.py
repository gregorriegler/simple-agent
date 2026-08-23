from typing import Protocol

from .observer_definition import ObserverDefinition


class ObserverLibrary(Protocol):
    def read_observer_definition(self, name: str) -> ObserverDefinition: ...
