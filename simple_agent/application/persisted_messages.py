from .agent_id import AgentId
from .llm import ChatMessages, Messages
from .session_storage import SessionStorage


class PersistedMessages(Messages):
    def __init__(
        self,
        session_storage: SessionStorage,
        agent_id: AgentId,
        messages: ChatMessages | None = None,
        system_prompt: str | None = None,
    ):
        super().__init__(messages, system_prompt)
        self._session_storage = session_storage
        self._agent_id = agent_id

    def user_says(self, content: str):
        super().user_says(content)
        self._session_storage.save_messages(self._agent_id, self)

    def assistant_says(self, content: str):
        super().assistant_says(content)
        self._session_storage.save_messages(self._agent_id, self)

    def add(self, role: str, content: str):
        super().add(role, content)
        self._session_storage.save_messages(self._agent_id, self)

    def clear(self):
        super().clear()
        self._session_storage.save_messages(self._agent_id, self)
