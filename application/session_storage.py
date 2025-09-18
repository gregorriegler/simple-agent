from typing import Protocol

from .chat import Messages


class SessionStorage(Protocol):

    def load(self) -> Messages:
        ...

    def save(self, messages: Messages) -> None:
        ...
