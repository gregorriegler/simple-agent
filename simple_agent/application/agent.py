import asyncio

from simple_agent.logging_config import get_logger
from .agent_id import AgentId
from .event_bus_protocol import EventBus
from .events import (
    AgentStartedEvent, AgentFinishedEvent,
    AssistantSaidEvent, AssistantRespondedEvent,
    ToolCalledEvent, ToolResultEvent, ToolCancelledEvent,
    SessionEndedEvent, SessionInterruptedEvent,
    UserPromptRequestedEvent, UserPromptedEvent,
    ErrorEvent, SessionClearedEvent
)
from .input import Input
from .llm import LLM, Messages
from .tool_library import ToolResult, ContinueResult, ToolLibrary, MessageAndParsedTools, ParsedTool

logger = get_logger(__name__)


class ToolExecutionLog:
    def __init__(self):
        self._entries: list[tuple[ParsedTool, ToolResult]] = []
        self._last_result: ToolResult = ContinueResult()
        self._active_tool: ParsedTool | None = None

    def reset(self) -> None:
        self._entries.clear()
        self._last_result = ContinueResult()
        self._active_tool = None

    @property
    def last_result(self) -> ToolResult:
        return self._last_result

    def set_active_tool(self, tool: ParsedTool | None) -> None:
        self._active_tool = tool

    @property
    def active_tool(self) -> ParsedTool | None:
        return self._active_tool

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


class Agent:
    def __init__(
        self,
        agent_id: AgentId,
        agent_name: str,
        tools: ToolLibrary,
        llm: LLM,
        user_input: Input,
        event_bus: EventBus,
        context: Messages,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.llm: LLM = llm
        self.tools = tools
        self.user_input = user_input
        self.event_bus = event_bus
        self._tool_call_counter = 0
        self.context: Messages = context

    async def start(self):
        self._notify_agent_started()
        try:
            tool_result: ToolResult = ContinueResult()

            while True:
                try:
                    prompt = await self.user_prompts()
                    if not prompt:
                        break
                    tool_result = await self.run_tool_loop()
                except asyncio.CancelledError:
                    # ESC pressed - interrupt current operation but continue session
                    await self._notify_session_interrupted()
                    continue

            self._notify_session_ended()
            return tool_result
        except (EOFError, KeyboardInterrupt):
            self._notify_session_ended()
            return ContinueResult()
        finally:
            self._notify_agent_finished()

    async def user_prompts(self):
        if not self.user_input.has_stacked_messages():
            await self._notify_user_prompt_requested()
        prompt = await self.user_input.read_async()
        while prompt == "/clear":
            self.context.clear()
            self.event_bus.publish(SessionClearedEvent(self.agent_id))
            await self._notify_user_prompt_requested()
            prompt = await self.user_input.read_async()
        if prompt:
            self.context.user_says(prompt)
            await self._notify_user_prompted(prompt)
        return prompt

    async def run_tool_loop(self):
        log = ToolExecutionLog()
        tool_result: ToolResult = ContinueResult()

        try:
            while tool_result.do_continue():
                message, tools = await self.llm_responds()
                if message:
                    await self._notify_assistant_said(message)

                if not tools:
                    break

                log.reset()
                for tool in tools:
                    log.set_active_tool(tool)
                    tool_result = await self.execute_tool(tool)
                    log.set_active_tool(None)
                    log.add(tool, tool_result)
                    if not tool_result.do_continue():
                        break

                if message := log.format_continue_message():
                    self.context.user_says(message)

        except asyncio.CancelledError:
            if log.active_tool:
                self.context.user_says(log.active_tool.cancelled_message())
            raise
        except KeyboardInterrupt:
            await self._notify_session_interrupted()
            raise
        except Exception as e:
            await self._notify_error_occured(e)

        return tool_result

    async def llm_responds(self) -> MessageAndParsedTools:
        from simple_agent.application.model_info import ModelInfo

        response = await self.llm.call_async(self.context.to_list())
        answer = response.content
        model = response.model
        token_count = response.usage.total_tokens if response.usage else 0
        max_tokens = ModelInfo.get_context_window(model)

        self.context.assistant_says(answer)
        self.event_bus.publish(AssistantRespondedEvent(
            self.agent_id,
            answer,
            model=model,
            token_count=token_count,
            max_tokens=max_tokens
        ))
        return self.tools.parse_message_and_tools(answer)

    async def execute_tool(self, tool: ParsedTool) -> ToolResult:
        self._tool_call_counter += 1
        call_id = f"{self.agent_id}::tool_call::{self._tool_call_counter}"
        await self._notify_tool_called(call_id, tool)
        try:
            tool_result = await self.tools.execute_parsed_tool(tool)
            await self._notify_tool_completed(call_id, tool_result)
            return tool_result
        except asyncio.CancelledError:
            await self._notify_tool_cancelled(call_id)
            raise

    def _notify_agent_started(self):
        self.event_bus.publish(AgentStartedEvent(self.agent_id, self.agent_name, self.llm.model))

    async def _notify_user_prompt_requested(self):
        self.event_bus.publish(UserPromptRequestedEvent(self.agent_id))

    async def _notify_user_prompted(self, prompt):
        self.event_bus.publish(UserPromptedEvent(self.agent_id, prompt))

    async def _notify_assistant_said(self, message):
        self.event_bus.publish(AssistantSaidEvent(self.agent_id, message))

    async def _notify_tool_cancelled(self, call_id):
        self.event_bus.publish(ToolCancelledEvent(self.agent_id, call_id))

    async def _notify_tool_completed(self, call_id, tool_result):
        self.event_bus.publish(ToolResultEvent(self.agent_id, call_id, tool_result))

    async def _notify_tool_called(self, call_id, tool):
        self.event_bus.publish(ToolCalledEvent(self.agent_id, call_id, tool))

    def _notify_agent_finished(self):
        self.event_bus.publish(AgentFinishedEvent(self.agent_id))

    def _notify_session_ended(self):
        self.event_bus.publish(SessionEndedEvent(self.agent_id))

    async def _notify_error_occured(self, e):
        self.event_bus.publish(ErrorEvent(self.agent_id, str(e)))

    async def _notify_session_interrupted(self):
        self.event_bus.publish(SessionInterruptedEvent(self.agent_id))
