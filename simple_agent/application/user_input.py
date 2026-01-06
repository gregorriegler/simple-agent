from typing import Protocol


class UserInput(Protocol):
    async def read_async(self) -> str: ...

    def escape_requested(self) -> bool: ...

    def close(self) -> None: ...


class DummyUserInput(UserInput):
    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        pass
