from pathlib import Path
from typing import Protocol

from .agent_id import AgentId
from .llm import Messages


class SessionStorage(Protocol):
    def load_messages(self, agent_id: AgentId) -> Messages: ...

    def save_messages(self, agent_id: AgentId, messages: Messages) -> None: ...

    def session_root(self) -> Path: ...


class NoOpSessionStorage:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path.cwd()

    def load_messages(self, agent_id: AgentId) -> Messages:
        return Messages()

    def save_messages(self, agent_id: AgentId, messages: Messages) -> None:
        return None

    def session_root(self) -> Path:
        return self._root
