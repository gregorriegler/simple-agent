from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .agent_id import AgentId
from .llm import Messages


@dataclass
class AgentMetadata:
    model: str = ""
    max_tokens: int = 0
    input_tokens: int = 0


class SessionStorage(Protocol):
    def load_messages(self, agent_id: AgentId) -> Messages: ...

    def save_messages(self, agent_id: AgentId, messages: Messages) -> None: ...

    def load_metadata(self, agent_id: AgentId) -> AgentMetadata: ...

    def save_metadata(self, agent_id: AgentId, metadata: AgentMetadata) -> None: ...

    def session_root(self) -> Path: ...

    def list_stored_agents(self) -> list[AgentId]: ...


class NoOpSessionStorage:
    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path.cwd()

    def load_messages(self, agent_id: AgentId) -> Messages:
        return Messages()

    def save_messages(self, agent_id: AgentId, messages: Messages) -> None:
        return None

    def load_metadata(self, agent_id: AgentId) -> AgentMetadata:
        return AgentMetadata()

    def save_metadata(self, agent_id: AgentId, metadata: AgentMetadata) -> None:
        return None

    def session_root(self) -> Path:
        return self._root

    def list_stored_agents(self) -> list[AgentId]:
        return []
