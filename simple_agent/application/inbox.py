import asyncio


class Inbox:
    """Messages waiting for an agent, from other agents, observers, or tools."""

    def __init__(self):
        self._messages: list[str] = []
        self._arrived = asyncio.Event()

    def put(self, message: str) -> None:
        self._messages.append(message)
        self._arrived.set()

    def take(self) -> str:
        message = self._messages.pop()
        if not self._messages:
            self._arrived.clear()
        return message

    def is_empty(self) -> bool:
        return not self._messages

    def drain(self) -> list[str]:
        messages, self._messages = self._messages, []
        self._arrived.clear()
        return messages

    async def wait(self) -> None:
        """Block until a message is waiting."""
        await self._arrived.wait()
