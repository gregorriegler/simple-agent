import asyncio
import threading
import time

import pytest

from simple_agent.tools.base_tool import BaseTool


@pytest.mark.asyncio
async def test_run_command_async_does_not_block_event_loop(monkeypatch):
    other_ran = threading.Event()

    def blocking_run_command(command, args=None, cwd=None):
        time.sleep(0.05)
        return {
            "output": str(other_ran.is_set()),
            "success": True,
            "elapsed_time": 0.05,
        }

    monkeypatch.setattr(BaseTool, "run_command", staticmethod(blocking_run_command))

    async def set_event_next_tick() -> None:
        await asyncio.sleep(0)
        other_ran.set()

    other_task = asyncio.create_task(set_event_next_tick())
    result = await BaseTool.run_command_async("noop")
    await other_task

    assert result["output"] == "True"
