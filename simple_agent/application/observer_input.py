import asyncio

from .user_input import UserInput

CLOSED = ""


class ObserverInput(UserInput):
    """What an observer reads: packets about the observed agent, or what the user types on its tab."""

    def __init__(self, user_input: UserInput):
        self._packets: list[str] = []
        self._user_input = user_input
        self._typed: asyncio.Future[str] | None = None
        self._waiter: asyncio.Future[None] | None = None

    def submit(self, packet: str) -> None:
        self._packets.append(packet)
        self._wake()

    async def read_async(self) -> str:
        if self._packets:
            return self._take_latest()
        typed = self._user_input_reading()
        waiter = asyncio.get_running_loop().create_future()
        self._waiter = waiter
        typed.add_done_callback(self._wake_on)
        try:
            await waiter
        finally:
            self._waiter = None
            typed.remove_done_callback(self._wake_on)
        if typed.done():
            self._typed = None
            return typed.result()
        return self._take_latest()

    def _user_input_reading(self) -> asyncio.Future[str]:
        if self._typed is None:
            self._typed = asyncio.ensure_future(self._user_input.read_async())
        return self._typed

    def _wake_on(self, _: asyncio.Future) -> None:
        self._wake()

    def _wake(self) -> None:
        if self._waiter is not None and not self._waiter.done():
            self._waiter.set_result(None)

    def _take_latest(self) -> str:
        latest = CLOSED
        while self._packets and self._packets[0] != CLOSED:
            latest = self._packets.pop(0)
        if latest == CLOSED:
            self._stop_reading_user_input()
        return latest

    def _stop_reading_user_input(self) -> None:
        if self._typed is not None:
            self._typed.cancel()
            self._typed = None

    def drain(self) -> list[str]:
        return self._user_input.drain()

    def escape_requested(self) -> bool:
        return self._user_input.escape_requested()

    def close(self) -> None:
        self.submit(CLOSED)
