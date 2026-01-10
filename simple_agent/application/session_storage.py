from pathlib import Path
from typing import Protocol


class SessionStorage(Protocol):
    def session_root(self) -> Path: ...
