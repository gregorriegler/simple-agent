import asyncio
from collections.abc import Callable

from .agent_id import AgentId
from .event_bus import EventBus
from .events import ToolCalledEvent, ToolCancelledEvent, ToolResultEvent
from .tool_library import RawToolCall, ToolCall, ToolLibrary
from .tool_results import ManyToolsResult, ToolResult, TruncatedToolResult

INTERRUPTED_RESULT = "Interrupted by the user before the tool finished."

OnResult = Callable[[RawToolCall, str], None]


class ToolsExecutor:
    def __init__(
        self,
        library: ToolLibrary,
        event_bus: EventBus,
        agent_id: AgentId,
        on_result: OnResult | None = None,
    ):
        self._library = library
        self._event_bus = event_bus
        self._agent_id = agent_id
        self._on_result = on_result or (lambda call, output: None)
        self._tool_call_counter = 0

    async def execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
    ) -> ManyToolsResult:
        result = ManyToolsResult()
        for index, tool_call in enumerate(tool_calls):
            try:
                single_result = await self._execute(tool_call)
                result.add(tool_call, single_result)
                self._on_result(tool_call.raw_call, str(single_result))
            except asyncio.CancelledError:
                result.mark_cancelled(tool_call)
                for unanswered in tool_calls[index:]:
                    self._on_result(unanswered.raw_call, INTERRUPTED_RESULT)
                raise
        return result

    async def _execute(self, tool_call: ToolCall) -> ToolResult:
        self._tool_call_counter += 1
        call_id = f"{self._agent_id}::tool_call::{self._tool_call_counter}"
        self._event_bus.publish(
            ToolCalledEvent(self._agent_id, call_id, tool_call.raw_call)
        )
        try:
            tool_result = TruncatedToolResult(
                await self._library.execute_tool_call(tool_call)
            )
            self._event_bus.publish(
                ToolResultEvent(self._agent_id, call_id, tool_result)
            )
            return tool_result
        except asyncio.CancelledError:
            self._event_bus.publish(ToolCancelledEvent(self._agent_id, call_id))
            raise
