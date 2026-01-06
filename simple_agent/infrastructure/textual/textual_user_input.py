import asyncio
from queue import Empty, Queue

from simple_agent.application.user_input import UserInput


class TextualUserInput(UserInput):
    def __init__(self):
        self.input_queue: Queue[str] = Queue()
        self.escape_flag = False
        self.closing = False

    async def read_async(self) -> str:
        while not self.closing:
            try:
                return self.input_queue.get_nowait()
            except Empty:
                await asyncio.sleep(0.05)
        return ""

    def submit_input(self, message: str):
        self.escape_flag = False
        self.input_queue.put(message)

    def escape_requested(self) -> bool:
        return self.escape_flag

    def close(self):
        self.closing = True
