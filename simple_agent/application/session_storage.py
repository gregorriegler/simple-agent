from pathlib import Path
from typing import Protocol

from .agent_id import AgentId


class SessionStorage(Protocol):
    def session_root(self) -> Path: ...

    def list_stored_agents(self) -> list[AgentId]: ...


class NoOpSessionStorage:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path.cwd()

    def session_root(self) -> Path:
        return self._root

    def list_stored_agents(self) -> list[AgentId]:
        return []
