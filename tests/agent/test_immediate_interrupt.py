import asyncio
import time
from unittest.mock import Mock

import pytest

from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.llm import Messages
from simple_agent.application.tool_library import ContinueResult


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
        self._escape_count = 0

    def has_stacked_messages(self) -> bool:
        return self._read_count == 0

    def read(self) -> str:
        self._read_count += 1
        if self._read_count == 1:
            return "Hello"
        return ""

    def escape_requested(self) -> bool:
        self._escape_count += 1
        return True


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
async def test_escape_interrupts_during_llm_call():
    event_bus = SimpleEventBus()

    agent = Agent(
        agent_id=AgentId("test"),
        agent_name="Test Agent",
        tools=_make_tool_library(),
        llm=SlowLLM(),
        user_input=InputWithStartMessage(),
        event_bus=event_bus,
        session_storage=Mock(),
        context=Messages("system prompt"),
    )

    start = time.monotonic()
    await agent.start()
    elapsed = time.monotonic() - start

    assert elapsed < 2.0, (
        f"Cancellation took {elapsed:.1f}s - expected < 2s. "
        "ESC should cancel the LLM call immediately, not wait for it to complete."
    )


class SlowTool:

    async def __call__(self, **kwargs):
        await asyncio.sleep(10)
        return ContinueResult("This should not be reached")


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

    def execute_parsed_tool(self, tool):
        return self._slow_tool()


class InputForToolTest:

    def __init__(self):
        self._read_count = 0

    def has_stacked_messages(self) -> bool:
        return self._read_count == 0

    def read(self) -> str:
        self._read_count += 1
        if self._read_count == 1:
            return "call the slow tool"
        return ""

    def escape_requested(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_escape_interrupts_during_tool_execution():
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
        session_storage=Mock(),
        context=Messages("system prompt"),
    )

    start = time.monotonic()
    await agent.start()
    elapsed = time.monotonic() - start

    assert elapsed < 2.0, (
        f"Cancellation took {elapsed:.1f}s - expected < 2s. "
        "ESC should cancel the tool execution immediately, not wait for it to complete."
    )
