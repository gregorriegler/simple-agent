import asyncio
from queue import Empty, Queue

from simple_agent.application.agent_id import AgentId
from simple_agent.application.user_input import UserInput


class TextualUserInput(UserInput):
    def __init__(self):
        self.input_queues: dict[AgentId, Queue[str]] = {}
        self.escape_flag = False
        self.closing = False

    def _queue_for(self, agent_id: AgentId) -> Queue[str]:
        if agent_id not in self.input_queues:
            self.input_queues[agent_id] = Queue()
        return self.input_queues[agent_id]

    async def read_async(self, agent_id: AgentId) -> str:
        queue = self._queue_for(agent_id)
        while not self.closing:
            try:
                return queue.get_nowait()
            except Empty:
                await asyncio.sleep(0.05)
        return ""

    def submit_input(self, agent_id: AgentId, message: str):
        self.escape_flag = False
        self._queue_for(agent_id).put(message)

    def escape_requested(self) -> bool:
        return self.escape_flag

    def close(self):
        self.closing = True
