import asyncio

from simple_agent.logging_config import get_logger

from .agent_id import AgentId
from .agent_type import AgentType
from .event_bus import EventBus
from .events import (
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    ErrorEvent,
    ModelChangedEvent,
    SessionClearedEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    UserPromptedEvent,
    UserPromptRequestedEvent,
)
from .input import Input
from .llm import LLM, LLMProvider, Messages
from .slash_command_registry import CommandParseError, SlashCommandRegistry
from .slash_commands import ClearCommand, ModelCommand, SlashCommandVisitor
from .tool_library import MessageAndParsedTools, ToolLibrary
from .tool_results import SingleToolResult, ToolResult, ToolResultStatus
from .tools_executor import ToolsExecutor

logger = get_logger(__name__)


class Agent(SlashCommandVisitor):
    def __init__(
        self,
        agent_id: AgentId,
        agent_name: str,
        tools: ToolLibrary,
        llm_provider: LLMProvider,
        model_name: str,
        user_input: Input,
        event_bus: EventBus,
        context: Messages,
        agent_type: AgentType | None = None,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.llm: LLM = llm_provider.get(model_name)
        self.tools = tools
        self.user_input = user_input
        self.event_bus = event_bus
        self.tools_executor = ToolsExecutor(self.tools, self.event_bus, self.agent_id)
        self.context: Messages = context
        self.slash_command_registry = SlashCommandRegistry(
            available_models=llm_provider.get_available_models()
        )

    async def start(self):
        self._notify_agent_started()
        try:
            tool_result: ToolResult = SingleToolResult()

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

            return tool_result
        except (EOFError, KeyboardInterrupt):
            return SingleToolResult()
        finally:
            self._notify_agent_finished()
            self._notify_session_ended()

    async def user_prompts(self):
        if not self.user_input.has_stacked_messages():
            await self._notify_user_prompt_requested()
        prompt = await self.user_input.read_async()

        while prompt and self._is_slash_command(prompt):
            await self._handle_slash_command(prompt)
            await self._notify_user_prompt_requested()
            prompt = await self.user_input.read_async()

        if prompt:
            self.context.user_says(prompt)
            await self._notify_user_prompted(prompt)
        return prompt

    def _is_slash_command(self, prompt: str) -> bool:
        """Check if the prompt is a registered slash command."""
        if not prompt.startswith("/"):
            return False

        command_name = prompt.split()[0]
        all_commands = self.slash_command_registry.get_all_commands()
        return command_name in all_commands

    async def _handle_slash_command(self, prompt: str):
        try:
            command = self.slash_command_registry.parse(prompt)
            await command.accept(self)
        except CommandParseError as e:
            await self._notify_error_occured(str(e))

    async def clear_conversation(self, command: ClearCommand) -> None:
        self.context.clear()
        self.event_bus.publish(SessionClearedEvent(self.agent_id))

    async def change_model(self, command: ModelCommand) -> None:
        old_model = self.llm.model
        try:
            self.llm = self.llm_provider.get(command.model_name)
            self.event_bus.publish(
                ModelChangedEvent(self.agent_id, old_model, command.model_name)
            )
        except Exception as e:
            await self._notify_error_occured(str(e))

    async def run_tool_loop(self):
        try:
            tool_result: ToolResult = SingleToolResult()
            while tool_result.do_continue():
                response = await self.llm_responds()
                message = response.message
                tools = response.tools
                if message:
                    await self._notify_assistant_said(message)

                if not tools:
                    break

                tool_result = await self.tools_executor.execute_tools(tools)
                self.context.user_says(tool_result.message)

            return tool_result
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            await self._notify_session_interrupted()
            raise
        except Exception as e:
            await self._notify_error_occured(e)
            return SingleToolResult(
                message=str(e),
                status=ToolResultStatus.FAILURE,
                completes=True,
            )

    async def llm_responds(self) -> MessageAndParsedTools:
        from simple_agent.application.model_info import ModelInfo

        response = await self.llm.call_async(self.context.to_list())
        answer = response.content
        model = response.model

        input_tokens = 0
        if response.usage:
            input_tokens = response.usage.input_tokens

        max_tokens = ModelInfo.get_context_window(model)
        if response.usage and response.usage.input_token_limit:
            max_tokens = response.usage.input_token_limit

        token_usage_display = self._format_token_usage(input_tokens, max_tokens)
        self.context.assistant_says(answer)
        self.event_bus.publish(
            AssistantRespondedEvent(
                self.agent_id,
                answer,
                model=model,
                token_usage_display=token_usage_display,
            )
        )
        return self.tools.parse_message_and_tools(answer)

    @staticmethod
    def _format_token_usage(input_tokens: int, max_tokens: int) -> str:
        if max_tokens == 0:
            return "0.0%"
        percentage = (input_tokens / max_tokens) * 100
        return f"{percentage:.1f}%"

    def _notify_agent_started(self):
        self.event_bus.publish(
            AgentStartedEvent(
                self.agent_id,
                self.agent_name,
                self.llm.model,
                self.agent_type,
            )
        )

    async def _notify_user_prompt_requested(self):
        self.event_bus.publish(UserPromptRequestedEvent(self.agent_id))

    async def _notify_user_prompted(self, prompt):
        self.event_bus.publish(UserPromptedEvent(self.agent_id, prompt))

    async def _notify_assistant_said(self, message):
        self.event_bus.publish(AssistantSaidEvent(self.agent_id, message))

    def _notify_agent_finished(self):
        self.event_bus.publish(AgentFinishedEvent(self.agent_id))

    def _notify_session_ended(self):
        self.event_bus.publish(SessionEndedEvent(self.agent_id))

    async def _notify_error_occured(self, e):
        self.event_bus.publish(ErrorEvent(self.agent_id, str(e)))

    async def _notify_session_interrupted(self):
        self.event_bus.publish(SessionInterruptedEvent(self.agent_id))
