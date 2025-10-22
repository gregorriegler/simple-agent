from typing import Protocol


class SystemPrompt(Protocol):

    def __call__(self) -> str:
        ...
