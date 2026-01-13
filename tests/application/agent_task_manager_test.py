import asyncio

import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_task_manager import AgentTaskManager


@pytest.mark.asyncio
async def test_start_task_registers_task():
    manager = AgentTaskManager()
    agent_id = AgentId("test-agent")

    async def sample_coro():
        await asyncio.sleep(0.1)

    task = manager.start_task(agent_id, sample_coro())

    assert agent_id in manager._tasks
    assert manager._tasks[agent_id] == task
    await task


@pytest.mark.asyncio
async def test_task_removed_on_completion():
    manager = AgentTaskManager()
    agent_id = AgentId("test-agent")

    async def sample_coro():
        return "done"

    task = manager.start_task(agent_id, sample_coro())
    await task

    # Small sleep to allow done_callback to run
    await asyncio.sleep(0.01)
    assert agent_id not in manager._tasks


@pytest.mark.asyncio
async def test_cancel_task():
    manager = AgentTaskManager()
    agent_id = AgentId("test-agent")

    task_started = asyncio.Event()

    async def sample_coro():
        task_started.set()
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise

    task = manager.start_task(agent_id, sample_coro())
    await task_started.wait()

    cancelled = manager.cancel_task(agent_id)
    assert cancelled is True

    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_cancel_non_existent_task():
    manager = AgentTaskManager()
    agent_id = AgentId("non-existent")

    cancelled = manager.cancel_task(agent_id)
    assert cancelled is False


@pytest.mark.asyncio
async def test_cancel_all_tasks():
    manager = AgentTaskManager()
    agent_id1 = AgentId("agent-1")
    agent_id2 = AgentId("agent-2")

    async def sample_coro():
        await asyncio.sleep(1)

    task1 = manager.start_task(agent_id1, sample_coro())
    task2 = manager.start_task(agent_id2, sample_coro())

    manager.cancel_all_tasks()

    with pytest.raises(asyncio.CancelledError):
        await asyncio.gather(task1, task2)
