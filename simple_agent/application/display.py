from typing import Protocol


class Display(Protocol):

    def assistant_says(self, message) -> None:
        ...

    def tool_result(self, result) -> None:
        ...

    def input(self) -> str:
        ...

    def exit(self) -> None:
        ...
