import asyncio
import logging
from collections.abc import Coroutine

from simple_agent.application.agent_id import AgentId

logger = logging.getLogger(__name__)


class AgentTaskManager:
    def __init__(self):
        self._tasks: dict[AgentId, asyncio.Task] = {}

    def start_task(self, agent_id: AgentId, coroutine: Coroutine) -> asyncio.Task:
        task = asyncio.create_task(coroutine)
        self._tasks[agent_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(agent_id, None))
        return task

    def cancel_task(self, agent_id: AgentId) -> bool:
        task = self._tasks.get(agent_id)
        if task:
            task.cancel()
            return True
        logger.warning(f"No task found for agent ID: {agent_id}")
        return False

    def cancel_all_tasks(self):
        for task in list(self._tasks.values()):
            task.cancel()
