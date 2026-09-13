import asyncio
import time

import pytest

from simple_agent.application.inbox import Inbox
from simple_agent.tools.wait_tool import WaitTool
from tests.tool_calls import wait

pytestmark = pytest.mark.asyncio


async def test_wait_returns_once_a_message_is_stacked():
    inbox = Inbox()
    tool = WaitTool(inbox)
    started = time.time()
    waiting = asyncio.create_task(tool.execute(wait(timeout=5)))
    await asyncio.sleep(0.1)
    inbox.put("Background command `x` finished")

    result = await waiting

    assert result.message == "A message arrived."
    assert time.time() - started < 2


async def test_wait_returns_at_once_when_the_user_typed_something():
    inbox = Inbox()
    inbox.put("hello")

    result = await WaitTool(inbox).execute(wait(timeout=5))

    assert result.message == "A message arrived."
    assert inbox.drain() == ["hello"]


async def test_wait_gives_up_after_the_timeout():
    inbox = Inbox()

    result = await WaitTool(inbox).execute(wait(timeout=0.2))

    assert result.message == "Nothing arrived within 0.2 seconds."


async def test_a_closed_inbox_is_not_a_message():
    inbox = Inbox()
    inbox.close()

    result = await WaitTool(inbox).execute(wait(timeout=0.2))

    assert result.message == "Nothing arrived within 0.2 seconds."


async def test_wait_on_a_closed_inbox_still_hears_a_background_result():
    inbox = Inbox()
    inbox.close()
    waiting = asyncio.create_task(WaitTool(inbox).execute(wait(timeout=5)))
    await asyncio.sleep(0.1)
    inbox.put("Background command `x` finished")

    result = await waiting

    assert result.message == "A message arrived."
