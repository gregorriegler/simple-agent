from typing import Protocol

from .llm import Messages


class SessionStorage(Protocol):

    def load(self) -> Messages:
        ...

    def save(self, messages: Messages) -> None:
        ...
