from typing import Protocol


class UserInput(Protocol):

    # TODO do we still need this?
    def read(self) -> str:
        ...

    async def read_async(self) -> str:
        ...

    def escape_requested(self) -> bool:
        ...

    def close(self) -> None:
        ...


class DummyUserInput(UserInput):
    # TODO do we still need this?
    def read(self) -> str:
        return ""

    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        pass
