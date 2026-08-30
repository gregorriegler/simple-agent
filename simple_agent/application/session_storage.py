from pathlib import Path
from typing import Protocol


class SessionStorage(Protocol):
    def session_root(self) -> Path: ...

    def rotate(self) -> None: ...


class FixedSessionStorage(SessionStorage):
    """A session that never rotates, for tests and single-session callers."""

    def __init__(self, root: Path):
        self._root = root

    def session_root(self) -> Path:
        return self._root

    def rotate(self) -> None:
        pass
