from typing import Protocol


class UserInput(Protocol):

    def read(self) -> str:
        ...

    def escape_requested(self) -> bool:
        ...

    def close(self) -> None:
        ...
