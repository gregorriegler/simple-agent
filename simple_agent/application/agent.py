import asyncio
from dataclasses import replace
from typing import Protocol

from simple_agent.logging_config import get_logger

from .agent_id import AgentId
from .agent_type import AgentType
from .brain import Brain
from .event_bus import EventBus
from .events import (
    AgentChangedEvent,
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
from .llm import LLMProvider, Messages
from .slash_command_registry import CommandParseError, SlashCommandRegistry
from .slash_commands import (
    AgentCommand,
    ClearCommand,
    ModelCommand,
    SlashCommandVisitor,
)
from .tool_library import MessageAndParsedTools
from .tool_results import SingleToolResult, ToolResult, ToolResultStatus
from .tools_executor import ToolsExecutor

logger = get_logger(__name__)


class BrainFactory(Protocol):
    def build_brain(self, agent_id: AgentId, agent_type: AgentType) -> Brain: ...


class Agent(SlashCommandVisitor):
    def __init__(
        self,
        agent_id: AgentId,
        brain: Brain,
        llm_provider: LLMProvider,
        user_input: Input,
        event_bus: EventBus,
        context: Messages,
        agent_type: AgentType | None = None,
        available_agents: list[str] | None = None,
        brain_factory: BrainFactory | None = None,
    ):
        self.agent_id = agent_id
        self.brain = brain
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.user_input = user_input
        self.event_bus = event_bus
        self.tools_executor = ToolsExecutor(brain.tools, event_bus, agent_id)
        self.context: Messages = context
        self.brain_factory = brain_factory
        self.slash_command_registry = SlashCommandRegistry(
            available_models=llm_provider.get_available_models(),
            available_agents=available_agents,
        )

    def update_brain(self, brain: Brain) -> None:
        old_name = self.brain.name
        old_model = self.brain.llm.model
        self.brain = brain
        self.tools_executor = ToolsExecutor(brain.tools, self.event_bus, self.agent_id)
        self.context.seed_system_prompt(brain.system_prompt)
        if old_model != brain.llm.model:
            self.event_bus.publish(
                ModelChangedEvent(self.agent_id, old_model, brain.llm.model)
            )
        self.event_bus.publish(
            AgentChangedEvent(self.agent_id, old_name=old_name, new_name=brain.name)
        )

    async def start(self):
        self.event_bus.publish(
            AgentStartedEvent(
                self.agent_id,
                self.brain.name,
                self.brain.llm.model,
                self.agent_type,
            )
        )
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
                    self.event_bus.publish(SessionInterruptedEvent(self.agent_id))
                    continue

            return tool_result
        except (EOFError, KeyboardInterrupt):
            return SingleToolResult()
        finally:
            self.event_bus.publish(AgentFinishedEvent(self.agent_id))
            self.event_bus.publish(SessionEndedEvent(self.agent_id))

    async def user_prompts(self):
        if not self.user_input.has_stacked_messages():
            self.event_bus.publish(UserPromptRequestedEvent(self.agent_id))
        prompt = await self.user_input.read_async()

        while prompt and self._is_slash_command(prompt):
            await self._handle_slash_command(prompt)
            self.event_bus.publish(UserPromptRequestedEvent(self.agent_id))
            prompt = await self.user_input.read_async()

        if prompt:
            self.context.user_says(prompt)
            self.event_bus.publish(UserPromptedEvent(self.agent_id, prompt))
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
            self.event_bus.publish(ErrorEvent(self.agent_id, str(e)))

    async def clear_conversation(self, command: ClearCommand) -> None:
        self.context.clear()
        self.event_bus.publish(SessionClearedEvent(self.agent_id))

    async def change_model(self, command: ModelCommand) -> None:
        old_model = self.brain.llm.model
        try:
            new_llm = self.llm_provider.get(command.model_name)
            self.brain = replace(self.brain, llm=new_llm)
            self.event_bus.publish(
                ModelChangedEvent(self.agent_id, old_model, command.model_name)
            )
        except Exception as e:
            self.event_bus.publish(ErrorEvent(self.agent_id, str(e)))

    async def visit_agent_command(self, command: AgentCommand) -> None:
        if self.brain_factory is None:
            self.event_bus.publish(
                ErrorEvent(self.agent_id, "Agent switching is not available")
            )
            return
        try:
            brain = self.brain_factory.build_brain(
                self.agent_id, AgentType(command.agent_name)
            )
            self.update_brain(brain)
        except Exception as e:
            self.event_bus.publish(ErrorEvent(self.agent_id, str(e)))

    async def run_tool_loop(self):
        try:
            tool_result: ToolResult = SingleToolResult()
            while tool_result.do_continue():
                response = await self.llm_responds()
                message = response.message
                tools = response.tools
                if message:
                    self.event_bus.publish(AssistantSaidEvent(self.agent_id, message))

                if not tools:
                    break

                tool_result = await self.tools_executor.execute_tools(tools)
                self.context.user_says(tool_result.message)

            return tool_result
        except asyncio.CancelledError:
            raise
        except KeyboardInterrupt:
            self.event_bus.publish(SessionInterruptedEvent(self.agent_id))
            raise
        except Exception as e:
            self.event_bus.publish(ErrorEvent(self.agent_id, str(e)))
            return SingleToolResult(
                message=str(e),
                status=ToolResultStatus.FAILURE,
                completes=True,
            )

    async def llm_responds(self) -> MessageAndParsedTools:
        from simple_agent.application.model_info import ModelInfo

        response, parsed = await self.brain.respond(self.context.to_list())
        answer = response.content

        input_tokens = response.usage.input_tokens if response.usage else 0
        max_tokens = ModelInfo.get_context_window(response.model)
        if response.usage and response.usage.input_token_limit:
            max_tokens = response.usage.input_token_limit

        token_usage_display = self._format_token_usage(input_tokens, max_tokens)
        self.context.assistant_says(answer)
        self.event_bus.publish(
            AssistantRespondedEvent(
                self.agent_id,
                answer,
                model=response.model,
                token_usage_display=token_usage_display,
            )
        )
        return parsed

    @staticmethod
    def _format_token_usage(input_tokens: int, max_tokens: int) -> str:
        if max_tokens == 0:
            return "0.0%"
        percentage = (input_tokens / max_tokens) * 100
        return f"{percentage:.1f}%"
