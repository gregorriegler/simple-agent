from .llm import Messages
from .session_storage import SessionStorage


class PersistedMessages:

    def __init__(self, messages: Messages, session_storage: SessionStorage):
        self._messages = messages
        self._session_storage = session_storage

    def user_says(self, content: str):
        self._messages.user_says(content)
        self._session_storage.save(self._messages)

    def assistant_says(self, content: str):
        self._messages.assistant_says(content)
        self._session_storage.save(self._messages)

    def add(self, role: str, content: str):
        self._messages.add(role, content)
        self._session_storage.save(self._messages)

    def to_list(self):
        return self._messages.to_list()

    def __len__(self):
        return len(self._messages)

    def __iter__(self):
        return iter(self._messages)

    def __str__(self):
        return str(self._messages)

