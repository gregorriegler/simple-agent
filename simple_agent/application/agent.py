import asyncio

from simple_agent.logging_config import get_logger

from .agent_id import AgentId
from .agent_library import AgentLibrary
from .agent_type import AgentType
from .agent_types import AgentTypes
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
from .llm import LLM, LLMProvider, Messages
from .project_tree import ProjectTree
from .slash_command_registry import SlashCommandRegistry
from .subagent_spawner import SubagentSpawner
from .tool_documentation import generate_tools_documentation
from .tool_library import MessageAndParsedTools, ToolLibrary
from .tool_library_factory import ToolContext, ToolLibraryFactory
from .tool_results import SingleToolResult, ToolResult, ToolResultStatus
from .tools_executor import ToolsExecutor

logger = get_logger(__name__)


class Agent:
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
        agent_library: AgentLibrary | None = None,
        tool_library_factory: ToolLibraryFactory | None = None,
        project_tree: ProjectTree | None = None,
        subagent_spawner: SubagentSpawner | None = None,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.llm_provider = llm_provider
        self.llm: LLM = llm_provider.get(model_name)
        self.tools = tools
        self.user_input = user_input
        self.event_bus = event_bus
        self.tools_executor = ToolsExecutor(self.tools, self.event_bus, self.agent_id)
        self.context: Messages = context
        self.agent_library = agent_library
        self.tool_library_factory = tool_library_factory
        self.project_tree = project_tree
        self.subagent_spawner = subagent_spawner
        self.slash_command_registry = SlashCommandRegistry(
            available_models=llm_provider.get_available_models(),
            available_agents=agent_library.list_agent_types()
            if agent_library
            else None,
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

            self._notify_session_ended()
            return tool_result
        except (EOFError, KeyboardInterrupt):
            self._notify_session_ended()
            return SingleToolResult()
        finally:
            self._notify_agent_finished()

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
        """Handle slash commands using the registry."""
        if prompt == "/clear":
            self.context.clear()
            self.event_bus.publish(SessionClearedEvent(self.agent_id))
        elif prompt.startswith("/model"):
            parts = prompt.split()
            if len(parts) < 2:
                await self._notify_error_occured("Usage: /model <model-name>")
            else:
                new_model = parts[1]
                old_model = self.llm.model
                try:
                    self.llm = self.llm_provider.get(new_model)
                    self.event_bus.publish(
                        ModelChangedEvent(self.agent_id, old_model, new_model)
                    )
                except Exception as e:
                    await self._notify_error_occured(str(e))
        elif prompt.startswith("/agent"):
            await self._handle_agent_command(prompt)

    async def _handle_agent_command(self, prompt: str):
        if (
            not self.agent_library
            or not self.tool_library_factory
            or not self.project_tree
            or not self.subagent_spawner
        ):
            await self._notify_error_occured("Agent switching is not available.")
            return

        parts = prompt.split()
        if len(parts) < 2:
            await self._notify_error_occured("Usage: /agent <agent-type>")
            return

        agent_type_str = parts[1]

        if agent_type_str not in self.agent_library.list_agent_types():
            await self._notify_error_occured(f"Unknown agent type: {agent_type_str}")
            return

        try:
            agent_type = AgentType(agent_type_str)
            definition = self.agent_library.read_agent_definition(agent_type)

            self.agent_name = definition.agent_name()

            # Update Model
            model_name = definition.model()
            if model_name:
                self.llm = self.llm_provider.get(model_name)

            # Update Tools
            tool_context = ToolContext(definition.tool_keys(), self.agent_id)
            tools = self.tool_library_factory.create(
                tool_context,
                self.subagent_spawner,
                AgentTypes(self.agent_library.list_agent_types()),
            )
            self.tools = tools
            self.tools_executor = ToolsExecutor(
                self.tools, self.event_bus, self.agent_id
            )

            # Update System Prompt
            tools_documentation = generate_tools_documentation(
                tools.tools, tools.tool_syntax
            )
            system_prompt = definition.prompt().render(
                tools_documentation, self.project_tree
            )
            self.context.seed_system_prompt(system_prompt)

            self.event_bus.publish(AgentChangedEvent(self.agent_id, definition))

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

        self.context.assistant_says(answer)
        self.event_bus.publish(
            AssistantRespondedEvent(
                self.agent_id,
                answer,
                model=model,
                max_tokens=max_tokens,
                input_tokens=input_tokens,
            )
        )
        return self.tools.parse_message_and_tools(answer)

    def _notify_agent_started(self):
        self.event_bus.publish(
            AgentStartedEvent(self.agent_id, self.agent_name, self.llm.model)
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
