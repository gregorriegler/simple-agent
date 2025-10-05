from typing import Protocol, TextIO


class IO(Protocol):

    def input(self, prompt: str) -> str:
        ...

    def print(self, message: str, *, file: TextIO | None = None) -> None:
        ...
