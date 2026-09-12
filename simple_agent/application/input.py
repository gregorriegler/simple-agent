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
        inbox = asyncio.ensure_future(self.inbox.wait())
        keyboard = asyncio.ensure_future(self._read_keyboard())
        try:
            await asyncio.wait({inbox, keyboard}, return_when=asyncio.FIRST_COMPLETED)
        finally:
            inbox.cancel()
            if not keyboard.done():
                keyboard.cancel()
            await asyncio.gather(inbox, keyboard, return_exceptions=True)
        if not keyboard.cancelled():
            typed = keyboard.result()
            if isinstance(typed, BaseException):
                raise typed
            return typed
        return self.inbox.take()

    async def _read_keyboard(self) -> str | BaseException:
        try:
            return await self.user_input.read_async()
        except (EOFError, KeyboardInterrupt) as interrupt:
            return interrupt

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
