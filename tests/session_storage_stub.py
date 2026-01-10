from pathlib import Path

from simple_agent.application.agent_id import AgentId
from simple_agent.application.llm import Messages
from simple_agent.application.session_storage import AgentMetadata


class SessionStorageStub:
    def __init__(self):
        self.saved = {}
        self._root = Path.cwd()

    def load_messages(self, agent_id: AgentId) -> Messages:
        return Messages()

    def save_messages(self, agent_id: AgentId, messages: Messages):
        self.saved[agent_id.raw] = "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in messages
        )

    def load_metadata(self, agent_id: AgentId) -> AgentMetadata:
        return AgentMetadata()

    def save_metadata(self, agent_id: AgentId, metadata: AgentMetadata) -> None:
        return None

    def session_root(self) -> Path:
        return self._root

    def list_stored_agents(self) -> list[AgentId]:
        return []
