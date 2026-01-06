import asyncio
import sys
from unittest.mock import Mock

import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import ToolCalledEvent, ToolResultEvent
from simple_agent.application.tool_library import (
    MessageAndParsedTools,
    ParsedTool,
    RawToolCall,
    Tool,
    ToolLibrary,
)
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus
from simple_agent.application.tool_syntax import ToolSyntax
from simple_agent.application.tools_executor import ToolsExecutor
from simple_agent.tools.base_tool import BaseTool


class ToolLibraryStub(ToolLibrary):
    def __init__(self):
        self.tools: list[Tool] = []
        self.tool_syntax: ToolSyntax = Mock()

    def parse_message_and_tools(self, text: str) -> MessageAndParsedTools:
        return MessageAndParsedTools(text, [])

    async def execute_parsed_tool(self, parsed_tool):
        return await parsed_tool.tool_instance.execute(parsed_tool.raw_call)


class BlockingSlowTool:
    def __init__(self, delay_seconds: float = 0.1):
        self._delay_seconds = delay_seconds

    async def execute(self, raw_call):
        command = [
            sys.executable,
            "-c",
            f"import time; time.sleep({self._delay_seconds})",
        ]
        await BaseTool.run_command_async(command[0], command[1:])
        return SingleToolResult("done", status=ToolResultStatus.SUCCESS)


@pytest.mark.asyncio
async def test_tool_called_event_published_before_tool_completes():
    event_bus = SimpleEventBus()
    called_event = asyncio.Event()
    result_event = asyncio.Event()

    event_bus.subscribe(ToolCalledEvent, lambda event: called_event.set())
    event_bus.subscribe(ToolResultEvent, lambda event: result_event.set())

    tool = BlockingSlowTool(delay_seconds=0.1)
    parsed_tool = ParsedTool(RawToolCall(name="blocking", arguments=""), tool)

    executor = ToolsExecutor(
        library=ToolLibraryStub(),
        event_bus=event_bus,
        agent_id=AgentId("test"),
    )

    task = asyncio.create_task(executor.execute_tools([parsed_tool]))
    await asyncio.sleep(0)
    assert called_event.is_set() is True
    assert result_event.is_set() is False

    await task

    assert result_event.is_set() is True
