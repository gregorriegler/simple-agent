import asyncio

from .inbox import Inbox
from .user_input import UserInput

POLL_INTERVAL = 0.05


class Input:
    def __init__(self, user_input: UserInput, inbox: Inbox | None = None):
        self.user_input = user_input
        self.inbox = inbox or Inbox()

    def stack(self, message: str):
        self.inbox.put(message)

    def has_stacked_messages(self) -> bool:
        return not self.inbox.is_empty()

    def drain(self) -> list[str]:
        return self.inbox.drain() + self.user_input.drain()

    async def read_async(self) -> str:
        if not self.inbox.is_empty():
            return self.inbox.take()
        return await self.user_input.read_async()

    async def wait_for_message(self, timeout: float) -> bool:
        """Block until a message is waiting or the timeout passes."""
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            if not self.inbox.is_empty() or self.user_input.has_pending():
                return True
            if asyncio.get_running_loop().time() >= deadline:
                return False
            await asyncio.sleep(POLL_INTERVAL)

    def escape_requested(self) -> bool:
        return self.user_input.escape_requested()
