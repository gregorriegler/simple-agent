import asyncio
from queue import Empty, Queue

from simple_agent.application.agent_id import AgentId
from simple_agent.application.user_input import UserInput


class TextualUserInput(UserInput):
    def __init__(self):
        self.input_queues: dict[AgentId, Queue[str]] = {}
        self.default_queue: Queue[str] = Queue()
        self.escape_flag = False
        self.closing = False

    async def read_async(self, agent_id: AgentId | None = None) -> str:
        queue = self.default_queue
        if agent_id:
            if agent_id not in self.input_queues:
                self.input_queues[agent_id] = Queue()
            queue = self.input_queues[agent_id]

        while not self.closing:
            try:
                return queue.get_nowait()
            except Empty:
                await asyncio.sleep(0.05)
        return ""

    def submit_input(self, message: str, agent_id: AgentId | None = None):
        self.escape_flag = False
        if agent_id:
            if agent_id not in self.input_queues:
                self.input_queues[agent_id] = Queue()
            self.input_queues[agent_id].put(message)
        else:
            self.default_queue.put(message)

    def escape_requested(self) -> bool:
        return self.escape_flag

    def close(self):
        self.closing = True
