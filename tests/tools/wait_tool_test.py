import asyncio
import time

import pytest

from simple_agent.application.input import Input
from simple_agent.tools.wait_tool import WaitTool
from tests.tool_calls import wait
from tests.user_input_stub import UserInputStub

pytestmark = pytest.mark.asyncio


async def test_wait_returns_once_a_message_is_stacked():
    inbox = Input(UserInputStub())
    tool = WaitTool(inbox)
    started = time.time()
    waiting = asyncio.create_task(tool.execute(wait(timeout=5)))
    await asyncio.sleep(0.1)
    inbox.stack("Background command `x` finished")

    result = await waiting

    assert result.message == "A message arrived."
    assert time.time() - started < 2


async def test_wait_returns_at_once_when_the_user_typed_something():
    inbox = Input(UserInputStub(typed_while_working=["hello"]))

    result = await WaitTool(inbox).execute(wait(timeout=5))

    assert result.message == "A message arrived."
    assert inbox.drain() == ["hello"]


async def test_wait_gives_up_after_the_timeout():
    inbox = Input(UserInputStub())

    result = await WaitTool(inbox).execute(wait(timeout=0.2))

    assert result.message == "Nothing arrived within 0.2 seconds."
