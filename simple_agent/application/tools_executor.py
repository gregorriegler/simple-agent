import asyncio

from .agent_id import AgentId
from .event_bus import EventBus
from .events import ToolCalledEvent, ToolCancelledEvent, ToolResultEvent
from .tool_library import ParsedTool, ToolLibrary
from .tool_results import ManyToolsResult, ToolResult


class ToolsExecutor:
    def __init__(self, library: ToolLibrary, event_bus: EventBus, agent_id: AgentId):
        self._library = library
        self._event_bus = event_bus
        self._agent_id = agent_id
        self._tool_call_counter = 0

    async def execute_tools(
        self,
        tools: list[ParsedTool],
    ) -> ManyToolsResult:
        result = ManyToolsResult()
        for tool in tools:
            try:
                single_result = await self._execute(tool)
                result.add(tool, single_result)
            except asyncio.CancelledError:
                result.mark_cancelled(tool)
                raise
        return result

    async def _execute(self, tool: ParsedTool) -> ToolResult:
        self._tool_call_counter += 1
        call_id = f"{self._agent_id}::tool_call::{self._tool_call_counter}"
        self._event_bus.publish(ToolCalledEvent(self._agent_id, call_id, tool))
        try:
            tool_result = await self._library.execute_parsed_tool(tool)
            self._event_bus.publish(
                ToolResultEvent(self._agent_id, call_id, tool_result)
            )
            return tool_result
        except asyncio.CancelledError:
            self._event_bus.publish(ToolCancelledEvent(self._agent_id, call_id))
            raise
