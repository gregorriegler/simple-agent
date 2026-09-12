import asyncio

import pytest

from simple_agent.tools.bash_tool import BashTool
from tests.test_helpers import verify_tool
from tests.tool_calls import bash

pytestmark = pytest.mark.asyncio


async def test_bash_tool_background_execution(tool_library):
    await verify_tool(tool_library, bash("sleep 0.1", background=True))


async def test_background_command_reports_its_output_once_it_finishes():
    reported: list[str] = []
    tool = BashTool(report=reported.append)

    result = await tool.execute(bash("echo hi; exit 3", background=True))
    assert reported == []
    assert result.message.startswith("✅ Process started in background")

    await asyncio.gather(*_other_tasks())

    assert len(reported) == 1
    assert reported[0].startswith(
        "Background command `echo hi; exit 3` finished:\n❌ Exit code 3 ("
    )
    assert reported[0].endswith("s elapsed)\n\nhi")


def _other_tasks():
    return [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
