from typing import Protocol


class ChangeReporter(Protocol):
    def diff(self) -> str: ...
