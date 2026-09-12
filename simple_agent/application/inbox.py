class Inbox:
    """Messages waiting for an agent, from other agents, observers, or tools."""

    def __init__(self):
        self._messages: list[str] = []

    def put(self, message: str) -> None:
        self._messages.append(message)

    def take(self) -> str:
        return self._messages.pop()

    def is_empty(self) -> bool:
        return not self._messages

    def drain(self) -> list[str]:
        messages, self._messages = self._messages, []
        return messages
