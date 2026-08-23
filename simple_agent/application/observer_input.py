import asyncio

from .user_input import UserInput


class ObserverInput(UserInput):
    def __init__(self):
        self._packets: asyncio.Queue[str] = asyncio.Queue()

    def submit(self, packet: str) -> None:
        self._packets.put_nowait(packet)

    async def read_async(self) -> str:
        return await self._packets.get()

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        self._packets.put_nowait("")
