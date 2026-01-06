from .llm import Messages, ChatMessages
from .session_storage import SessionStorage


class PersistedMessages(Messages):
    def __init__(
        self,
        session_storage: SessionStorage,
        messages: ChatMessages | None = None,
        system_prompt: str | None = None,
    ):
        super().__init__(messages, system_prompt)
        self._session_storage = session_storage

    def user_says(self, content: str):
        super().user_says(content)
        self._session_storage.save(self)

    def assistant_says(self, content: str):
        super().assistant_says(content)
        self._session_storage.save(self)

    def add(self, role: str, content: str):
        super().add(role, content)
        self._session_storage.save(self)

    def clear(self):
        super().clear()
        self._session_storage.save(self)
