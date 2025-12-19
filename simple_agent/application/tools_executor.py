import asyncio

from .agent_id import AgentId
from .event_bus_protocol import EventBus
from .events import ToolCalledEvent, ToolResultEvent, ToolCancelledEvent
from .tool_library import ToolResult, ContinueResult, ToolLibrary, ParsedTool


class ToolExecutionLog:
    def __init__(self):
        self._entries: list[tuple[ParsedTool, ToolResult]] = []
        self._last_result: ToolResult = ContinueResult()
        self._cancelled_tool: ParsedTool | None = None

    @property
    def last_result(self) -> ToolResult:
        return self._last_result

    def add(self, tool: ParsedTool, result: ToolResult) -> None:
        self._entries.append((tool, result))
        self._last_result = result

    def format_continue_message(self) -> str | None:
        parts = [
            f"Result of {tool}\n{result}"
            for tool, result in self._entries
            if isinstance(result, ContinueResult)
        ]
        return "\n\n".join(parts) if parts else None

    def has_continue_results(self) -> bool:
        return any(isinstance(result, ContinueResult) for _, result in self._entries)

    def mark_cancelled(self, tool: ParsedTool) -> None:
        self._cancelled_tool = tool

    def was_cancelled(self) -> bool:
        return self._cancelled_tool is not None

    def cancelled_message(self) -> str:
        if not self._cancelled_tool:
            raise ValueError("cancelled_message called without a cancelled tool")
        return self._cancelled_tool.cancelled_message()


class ToolsExecutor:
    def __init__(self, library: ToolLibrary, event_bus: EventBus, agent_id: AgentId):
        self._library = library
        self._event_bus = event_bus
        self._agent_id = agent_id
        self._tool_call_counter = 0

    async def execute_tools(
        self,
        tools: list[ParsedTool],
    ) -> ToolExecutionLog:
        log = ToolExecutionLog()
        for tool in tools:
            try:
                result = await self.execute(tool)
                log.add(tool, result)
            except asyncio.CancelledError:
                log.mark_cancelled(tool)
                break

        return log

    async def execute(self, tool: ParsedTool) -> ToolResult:
        self._tool_call_counter += 1
        call_id = f"{self._agent_id}::tool_call::{self._tool_call_counter}"
        await self._notify_tool_called(call_id, tool)
        try:
            tool_result = await self._library.execute_parsed_tool(tool)
            await self._notify_tool_finished(call_id, tool_result)
            return tool_result
        except asyncio.CancelledError:
            await self._notify_tool_cancelled(call_id)
            raise

    async def _notify_tool_called(self, call_id, tool):
        self._event_bus.publish(ToolCalledEvent(self._agent_id, call_id, tool))

    async def _notify_tool_cancelled(self, call_id):
        self._event_bus.publish(ToolCancelledEvent(self._agent_id, call_id))

    async def _notify_tool_finished(self, call_id, tool_result):
        self._event_bus.publish(ToolResultEvent(self._agent_id, call_id, tool_result))
