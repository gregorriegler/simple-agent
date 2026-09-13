import asyncio

END_OF_INPUT = ""


class Inbox:
    """Messages waiting for an agent: what the user typed on its tab, what other agents, observers and tools sent."""

    def __init__(self):
        self._messages: list[str] = []
        self._arrived = asyncio.Event()
        self._message_arrived = asyncio.Event()
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

    async def read_async(self) -> str:
        await self.wait()
        return self.take()

    async def wait_for_message(self, timeout: float) -> bool:
        """Block until a message is waiting or the timeout passes; closing is not a message."""
        try:
            await asyncio.wait_for(self._message_arrived.wait(), timeout)
            return True
        except TimeoutError:
            return False

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
        if self.is_empty():
            self._message_arrived.clear()
        else:
            self._message_arrived.set()
