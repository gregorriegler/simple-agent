import asyncio

from .agent_event_publisher import AgentEventPublisher
from .agent_id import AgentId
from .event_bus import EventBus
from .events import ToolCalledEvent, ToolCancelledEvent, ToolResultEvent
from .tool_library import ParsedTool, ToolLibrary
from .tool_results import ManyToolsResult, ToolResult


class ToolsExecutor:
    def __init__(self, library: ToolLibrary, event_bus: EventBus, agent_id: AgentId):
        self._library = library
        self._publisher = AgentEventPublisher(agent_id, event_bus)
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
        self._publisher.publish(ToolCalledEvent(call_id=call_id, tool=tool))
        try:
            tool_result = await self._library.execute_parsed_tool(tool)
            self._publisher.publish(
                ToolResultEvent(call_id=call_id, result=tool_result)
            )
            return tool_result
        except asyncio.CancelledError:
            self._publisher.publish(ToolCancelledEvent(call_id=call_id))
            raise
