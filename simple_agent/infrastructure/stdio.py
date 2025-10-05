from typing import TextIO

from simple_agent.application.io import IO


class StdIO(IO):

    def input(self, prompt: str) -> str:
        return input(prompt)

    def print(self, message: str, *, file: TextIO | None = None) -> None:
        print(message, file=file)
