import asyncio
from collections.abc import Callable

from .agent_id import AgentId
from .event_bus import EventBus
from .events import ToolCalledEvent, ToolCancelledEvent, ToolResultEvent
from .tool_library import ToolCall, ToolInvocation, ToolLibrary
from .tool_results import ManyToolsResult, ToolResult, TruncatedToolResult

INTERRUPTED_RESULT = "Interrupted by the user before the tool finished."

OnResult = Callable[[ToolCall, str], None]


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
        invocations: list[ToolInvocation],
    ) -> ManyToolsResult:
        result = ManyToolsResult()
        for index, invocation in enumerate(invocations):
            try:
                single_result = await self._execute(invocation)
                result.add(invocation, single_result)
                self._on_result(invocation.call, str(single_result))
            except (asyncio.CancelledError, KeyboardInterrupt):
                result.mark_cancelled(invocation)
                for unanswered in invocations[index:]:
                    self._on_result(unanswered.call, INTERRUPTED_RESULT)
                raise
        return result

    async def _execute(self, invocation: ToolInvocation) -> ToolResult:
        self._tool_call_counter += 1
        call_id = f"{self._agent_id}::tool_call::{self._tool_call_counter}"
        self._event_bus.publish(
            ToolCalledEvent(self._agent_id, call_id, invocation.call)
        )
        try:
            tool_result = TruncatedToolResult(
                await self._library.execute_tool_call(invocation)
            )
            self._event_bus.publish(
                ToolResultEvent(self._agent_id, call_id, tool_result)
            )
            return tool_result
        except (asyncio.CancelledError, KeyboardInterrupt):
            self._event_bus.publish(ToolCancelledEvent(self._agent_id, call_id))
            raise
