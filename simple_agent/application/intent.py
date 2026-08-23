from typing import Protocol


class Intent(Protocol):
    def read(self) -> str: ...


class NoIntent(Intent):
    def read(self) -> str:
        return ""
