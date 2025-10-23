from typing import Protocol


class UserInput(Protocol):

    def read(self) -> str:
        ...

    def escape_requested(self) -> bool:
        ...

    def close(self) -> None:
        ...


class DummyUserInput(UserInput):
    def read(self) -> str:
        return ""
    def escape_requested(self) -> bool:
        return False
    def close(self) -> None:
        pass
