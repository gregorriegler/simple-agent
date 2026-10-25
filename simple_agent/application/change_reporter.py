from typing import Protocol


class ChangeReporter(Protocol):
    async def diff(self) -> str: ...
