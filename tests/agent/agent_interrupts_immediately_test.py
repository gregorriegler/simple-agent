import asyncio
import time
from unittest.mock import Mock

import pytest

from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import Messages
from simple_agent.application.tool_library import (
    MessageAndParsedTools,
    ParsedTool,
    RawToolCall,
    Tool,
)
from simple_agent.application.tool_results import SingleToolResult
from simple_agent.application.tool_syntax import ToolSyntax
from simple_agent.application.user_input import DummyUserInput


class SlowLLM:
    @property
    def model(self) -> str:
        return "slow-model"

    async def call_async(self, messages):
        await asyncio.sleep(10)
        return _make_response("This should not be reached")


def _make_response(content: str):
    return Mock(content=content, model="test-model", usage=Mock(total_tokens=10))


def _make_input_with_message(message: str) -> Input:
    user_input = DummyUserInput()
    feed = Input(user_input)
    feed.stack(message)
    return feed


class EmptyToolLibrary:
    def __init__(self):
        self.tools: list[Tool] = []
        self.tool_syntax: ToolSyntax = Mock()

    def parse_message_and_tools(self, text: str) -> MessageAndParsedTools:
        return MessageAndParsedTools(text, [])

    async def execute_parsed_tool(self, parsed_tool: ParsedTool):
        return SingleToolResult()


@pytest.mark.asyncio
async def test_cancel_interrupts_during_llm_call():
    """Cancelling the agent task should immediately interrupt a slow LLM call."""
    event_bus = SimpleEventBus()

    llm = SlowLLM()
    llm_provider = Mock()
    llm_provider.get.return_value = llm

    agent = Agent(
        agent_id=AgentId("test"),
        agent_name="Test Agent",
        tools=EmptyToolLibrary(),
        llm_provider=llm_provider,
        model_name="slow-model",
        user_input=_make_input_with_message("Hello"),
        event_bus=event_bus,
        context=Messages(system_prompt="system prompt"),
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
        self.tools: list[Tool] = []
        self.tool_syntax: ToolSyntax = Mock()

    def parse_message_and_tools(self, text: str) -> MessageAndParsedTools:
        if "<tool>slow_tool</tool>" in text:
            tool_call = RawToolCall(name="slow_tool", arguments="", body="")
            return MessageAndParsedTools("", [ParsedTool(tool_call, self._slow_tool)])
        return MessageAndParsedTools(text, [])

    async def execute_parsed_tool(self, parsed_tool: ParsedTool):
        return await self._slow_tool()


@pytest.mark.asyncio
async def test_cancel_interrupts_during_tool_execution():
    """Cancelling the agent task should immediately interrupt a slow tool call."""
    event_bus = SimpleEventBus()

    slow_tool = SlowTool()
    tool_library = ToolCallingToolLibrary(slow_tool)

    llm = ToolCallingLLM()
    llm_provider = Mock()
    llm_provider.get.return_value = llm

    agent = Agent(
        agent_id=AgentId("test"),
        agent_name="Test Agent",
        tools=tool_library,
        llm_provider=llm_provider,
        model_name="tool-calling-model",
        user_input=_make_input_with_message("call the slow tool"),
        event_bus=event_bus,
        context=Messages(system_prompt="system prompt"),
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
