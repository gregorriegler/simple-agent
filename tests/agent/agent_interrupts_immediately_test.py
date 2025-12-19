import asyncio
import time
from unittest.mock import Mock

import pytest

from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.llm import Messages
from simple_agent.application.tool_results import SingleToolResult


class SlowLLM:
    @property
    def model(self) -> str:
        return "slow-model"

    async def call_async(self, messages):
        await asyncio.sleep(10)
        return _make_response("This should not be reached")


class InputWithStartMessage:

    def __init__(self):
        self._read_count = 0

    def has_stacked_messages(self) -> bool:
        return self._read_count == 0

    async def read_async(self) -> str:
        self._read_count += 1
        if self._read_count == 1:
            return "Hello"
        return ""


def _make_response(content: str):
    return Mock(
        content=content,
        model="test-model",
        usage=Mock(total_tokens=10)
    )


def _make_tool_library():
    library = Mock()
    library.parse_message_and_tools.return_value = ("response", [])
    return library


@pytest.mark.asyncio
async def test_cancel_interrupts_during_llm_call():
    """Cancelling the agent task should immediately interrupt a slow LLM call."""
    event_bus = SimpleEventBus()

    agent = Agent(
        agent_id=AgentId("test"),
        agent_name="Test Agent",
        tools=_make_tool_library(),
        llm=SlowLLM(),
        user_input=InputWithStartMessage(),
        event_bus=event_bus,
        context=Messages("system prompt"),
    )

    start = time.monotonic()

    # Start agent as a task
    task = asyncio.create_task(agent.start())

    # Wait a bit then cancel
    await asyncio.sleep(0.1)
    task.cancel()

    # Wait for cancellation to complete
    try:
        await task
    except asyncio.CancelledError:
        pass

    elapsed = time.monotonic() - start

    assert elapsed < 1.0, (
        f"Cancellation took {elapsed:.1f}s - expected < 1s. "
        "task.cancel() should interrupt the LLM call immediately."
    )


class SlowTool:

    async def __call__(self, **kwargs):
        await asyncio.sleep(10)
        return SingleToolResult("This should not be reached")


class ToolCallingLLM:

    def __init__(self):
        self._call_count = 0

    @property
    def model(self) -> str:
        return "tool-calling-model"

    async def call_async(self, messages):
        self._call_count += 1
        if self._call_count == 1:
            return _make_response("<tool>slow_tool</tool>")
        return _make_response("Done")


class ToolCallingToolLibrary:

    def __init__(self, slow_tool: SlowTool):
        self._slow_tool = slow_tool

    def parse_message_and_tools(self, message: str):
        if "<tool>slow_tool</tool>" in message:
            return ("", [Mock(name="slow_tool")])
        return (message, [])

    async def execute_parsed_tool(self, tool):
        return await self._slow_tool()


class InputForToolTest:

    def __init__(self):
        self._read_count = 0

    def has_stacked_messages(self) -> bool:
        return self._read_count == 0

    async def read_async(self) -> str:
        self._read_count += 1
        if self._read_count == 1:
            return "call the slow tool"
        return ""


@pytest.mark.asyncio
async def test_cancel_interrupts_during_tool_execution():
    """Cancelling the agent task should immediately interrupt a slow tool call."""
    event_bus = SimpleEventBus()

    slow_tool = SlowTool()
    tool_library = ToolCallingToolLibrary(slow_tool)

    agent = Agent(
        agent_id=AgentId("test"),
        agent_name="Test Agent",
        tools=tool_library,
        llm=ToolCallingLLM(),
        user_input=InputForToolTest(),
        event_bus=event_bus,
        context=Messages("system prompt"),
    )

    start = time.monotonic()

    # Start agent as a task
    task = asyncio.create_task(agent.start())

    # Wait a bit then cancel
    await asyncio.sleep(0.1)
    task.cancel()

    # Wait for cancellation to complete
    try:
        await task
    except asyncio.CancelledError:
        pass

    elapsed = time.monotonic() - start

    assert elapsed < 1.0, (
        f"Cancellation took {elapsed:.1f}s - expected < 1s. "
        "task.cancel() should interrupt tool execution immediately."
    )
