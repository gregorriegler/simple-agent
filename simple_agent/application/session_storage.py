from typing import Protocol

from .llm import Messages


class SessionStorage(Protocol):

    def load(self) -> Messages:
        ...

    def save(self, messages: Messages) -> None:
        ...


class NoOpSessionStorage:

    def load(self) -> Messages:
        return Messages()

    def save(self, messages: Messages) -> None:
        return None
