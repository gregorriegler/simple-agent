import pytest

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.llm import (
    LLM,
    ChatMessages,
    LLMProvider,
    LLMResponse,
    TokenUsage,
)
from simple_agent.application.session import Session
from simple_agent.application.slash_command_registry import (
    SlashCommand,
    SlashCommandRegistry,
)
from simple_agent.application.slash_commands import model_handler
from simple_agent.application.todo_cleanup import TodoCleanup
from tests.session_storage_stub import SessionStorageStub
from tests.system_prompt_generator_test import GroundRulesStub
from tests.test_helpers import DummyProjectTree, create_session_args
from tests.test_tool_library import ToolLibraryFactoryStub
from tests.user_input_stub import UserInputStub


class MockLLM(LLM):
    def __init__(self, model_name: str):
        self._model_name = model_name
        self.calls = []

    @property
    def model(self) -> str:
        return self._model_name

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        self.calls.append(messages)
        return LLMResponse(
            content=f"Response from {self._model_name}",
            model=self._model_name,
            usage=TokenUsage(0, 0, 0),
        )


class MockLLMProvider(LLMProvider):
    def __init__(self):
        self.llms = {}

    def get(self, model_name: str | None = None) -> LLM:
        name = model_name or "default"
        if name not in self.llms:
            self.llms[name] = MockLLM(name)
        return self.llms[name]

    def get_available_models(self) -> list[str]:
        return list(self.llms.keys())


class TodoCleanupStub(TodoCleanup):
    def cleanup_all_todos(self) -> None:
        return None

    def cleanup_todos_for_agent(self, agent_id: AgentId) -> None:
        return None


class FakeAgentLibrary:
    def __init__(self):
        self._definitions = {
            "agent": AgentDefinition(
                AgentType("agent"), "---\nname: Agent\n---", GroundRulesStub("Prompt")
            ),
        }

    def list_agent_types(self):
        return list(self._definitions.keys())

    def read_agent_definition(self, agent_type):
        return self._definitions[agent_type.raw]

    def starting_agent_id(self):
        return AgentId("Agent")

    def _starting_agent_definition(self):
        return self._definitions["agent"]


@pytest.mark.asyncio
async def test_model_switching_uses_new_llm_instance():
    # Setup
    event_bus = SimpleEventBus()
    llm_provider = MockLLMProvider()

    # User inputs: initial message, command, subsequent message
    user_input = UserInputStub(
        inputs=["Hello", "/model specialized-gpt", "Do verify"],
        escapes=[False, False, False],
    )

    registry = SlashCommandRegistry()
    registry.register(SlashCommand("/model", "desc", model_handler))

    session = Session(
        event_bus=event_bus,
        session_storage=SessionStorageStub(),
        tool_library_factory=ToolLibraryFactoryStub(
            llm_provider.get("default"),
            inputs=[],
            escapes=[],
            interrupts=[],
            event_bus=event_bus,
        ),
        agent_library=FakeAgentLibrary(),
        user_input=user_input,
        todo_cleanup=TodoCleanupStub(),
        llm_provider=llm_provider,
        project_tree=DummyProjectTree(),
        slash_command_registry=registry,
    )

    # Run
    await session.run_async(
        create_session_args(False, start_message="Start"), AgentId("Agent")
    )

    # Verify
    default_llm = llm_provider.llms.get("default")
    specialized_llm = llm_provider.llms.get("specialized-gpt")

    assert default_llm is not None
    assert specialized_llm is not None

    # Default model should handle the start message and the first "Hello" (before switch)
    # Actually, let's trace:
    # 1. Start message -> Agent loop -> llm_responds (Default)
    # 2. User prompt "Hello" -> Agent loop -> llm_responds (Default)
    # 3. User prompt "/model specialized-gpt" -> Handled in user_prompts -> Switches model
    # 4. User prompt "Do verify" -> Agent loop -> llm_responds (Specialized)

    # Check default LLM calls
    # We expect at least one call (for "Start" or "Hello")
    assert len(default_llm.calls) >= 1

    # Check specialized LLM calls
    # We expect one call for "Do verify"
    assert len(specialized_llm.calls) == 1
    last_call_messages = specialized_llm.calls[0]
    # The last user message in that call should be "Do verify"
    assert last_call_messages[-1]["content"] == "Do verify"
