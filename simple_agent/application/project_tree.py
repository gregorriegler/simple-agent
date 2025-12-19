from typing import Protocol


class ProjectTree(Protocol):
    def render(self, max_depth: int = 2) -> str:
        ...
