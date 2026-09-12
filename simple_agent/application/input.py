import asyncio

from .inbox import Inbox
from .user_input import UserInput


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
        except asyncio.CancelledError:
            await self._settle(inbox, keyboard)
            typed = self._typed(keyboard)
            if isinstance(typed, str) and typed:
                self.inbox.put(typed)
            raise
        await self._settle(inbox, keyboard)
        typed = self._typed(keyboard)
        if typed is None:
            return self.inbox.take()
        if isinstance(typed, BaseException):
            raise typed
        return typed

    async def _read_keyboard(self) -> str | BaseException:
        try:
            return await self.user_input.read_async()
        except (EOFError, KeyboardInterrupt) as interrupt:
            return interrupt

    @staticmethod
    async def _settle(inbox: asyncio.Future, keyboard: asyncio.Future) -> None:
        inbox.cancel()
        if not keyboard.done():
            keyboard.cancel()
        await asyncio.gather(inbox, keyboard, return_exceptions=True)

    @staticmethod
    def _typed(keyboard: asyncio.Future) -> str | BaseException | None:
        return None if keyboard.cancelled() else keyboard.result()

    async def wait_for_message(self, timeout: float) -> bool:
        """Block until a message is waiting or the timeout passes."""
        deadline = asyncio.get_running_loop().time() + timeout
        try:
            message = await asyncio.wait_for(self.read_async(), timeout)
            if message:
                self.inbox.put(message)
                return True
            remaining = deadline - asyncio.get_running_loop().time()
            await asyncio.wait_for(self.inbox.wait(), max(remaining, 0))
            return True
        except TimeoutError:
            return False

    def escape_requested(self) -> bool:
        return self.user_input.escape_requested()
