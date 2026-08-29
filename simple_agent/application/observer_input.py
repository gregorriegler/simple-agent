import asyncio

from .user_input import UserInput


class ObserverInput(UserInput):
    def __init__(self):
        self._packets: asyncio.Queue[str] = asyncio.Queue()

    def submit(self, packet: str) -> None:
        self._packets.put_nowait(packet)

    async def read_async(self) -> str:
        packet = await self._packets.get()
        if packet == "":
            return ""
        while not self._packets.empty():
            next_packet = self._packets.get_nowait()
            if next_packet == "":
                self._packets.put_nowait("")
                break
            packet = next_packet
        return packet

    def escape_requested(self) -> bool:
        return False

    def close(self) -> None:
        self._packets.put_nowait("")
