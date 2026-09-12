import asyncio

from .user_input import UserInput

POLL_INTERVAL = 0.05


class Input:
    def __init__(self, user_input: UserInput):
        self.user_input = user_input
        self._stack: list[str] = []

    def stack(self, message: str):
        self._stack.append(message)

    def has_stacked_messages(self) -> bool:
        return bool(self._stack)

    def drain(self) -> list[str]:
        stacked, self._stack = self._stack, []
        return stacked + self.user_input.drain()

    async def read_async(self) -> str:
        if self._stack:
            return self._stack.pop()
        return await self.user_input.read_async()

    async def wait_for_message(self, timeout: float) -> bool:
        """Block until a message is waiting or the timeout passes."""
        deadline = asyncio.get_running_loop().time() + timeout
        while True:
            if self._stack or self.user_input.has_pending():
                return True
            if asyncio.get_running_loop().time() >= deadline:
                return False
            await asyncio.sleep(POLL_INTERVAL)

    def escape_requested(self) -> bool:
        return self.user_input.escape_requested()
