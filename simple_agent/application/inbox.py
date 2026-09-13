import asyncio

END_OF_INPUT = ""


class Inbox:
    """Messages waiting for an agent: what the user typed on its tab, what other agents, observers and tools sent."""

    def __init__(self):
        self._messages: list[str] = []
        self._arrived = asyncio.Event()
        self._closed = False

    def put(self, message: str) -> None:
        self._messages.append(message)
        self._refresh()

    def take(self) -> str:
        """The oldest waiting message, or an empty prompt once the inbox is closed and empty."""
        message = self._messages.pop(0) if self._messages else END_OF_INPUT
        self._refresh()
        return message

    def is_empty(self) -> bool:
        return not self._messages

    def drain(self) -> list[str]:
        messages, self._messages = self._messages, []
        self._refresh()
        return messages

    async def wait(self) -> None:
        """Block until a message is waiting or the inbox is closed."""
        await self._arrived.wait()

    def close(self) -> None:
        """No more messages will come; whoever waits gets an empty prompt after the rest."""
        self._closed = True
        self._refresh()

    def _has_something(self) -> bool:
        return bool(self._messages) or self._closed

    def _refresh(self) -> None:
        if self._has_something():
            self._arrived.set()
        else:
            self._arrived.clear()
