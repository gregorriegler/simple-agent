import pytest

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.event_store import NoOpEventStore
from simple_agent.application.events import AssistantRespondedEvent
from simple_agent.application.session import Session
from simple_agent.application.slash_command_registry import SlashCommandRegistry
from simple_agent.application.slash_commands import AgentCommand
from tests.application.model_switching_test import (
    FakeAgentLibrary,
    MockLLMProvider,
    TodoCleanupStub,
)
from tests.event_spy import EventSpy
from tests.system_prompt_generator_test import GroundRulesStub
from tests.test_helpers import DummyProjectTree, create_session_args
from tests.test_tool_library import ToolLibraryFactoryStub
from tests.user_input_stub import UserInputStub

pytestmark = pytest.mark.asyncio


class SwitchingAgentLibrary(FakeAgentLibrary):
    def __init__(self):
        super().__init__()
        self._definitions["developer"] = AgentDefinition(
            AgentType("developer"),
            """---\nname: Developer\nmodel: new-model\n---""",
            GroundRulesStub("Prompt"),
        )


async def test_slash_agent_command_parses_agent_name():
    registry = SlashCommandRegistry(available_agents=["developer", "review"])

    actual = registry.parse("/agent developer")

    assert isinstance(actual, AgentCommand)
    assert actual.agent_name == "developer"


async def test_agent_command_switches_model_for_follow_up_prompt():
    event_bus = SimpleEventBus()
    event_spy = EventSpy()
    event_bus.subscribe(AssistantRespondedEvent, event_spy.record_event)
    llm_provider = MockLLMProvider()
    user_input = UserInputStub(
        inputs=["Hello", "/agent developer", "Do verify"],
        escapes=[False, False, False],
    )
    agent_library = SwitchingAgentLibrary()

    session = Session(
        AgentId("Agent"),
        event_bus=event_bus,
        tool_library_factory=ToolLibraryFactoryStub(
            llm_provider.get("default-model"),
            inputs=[],
            escapes=[],
            interrupts=[],
            event_bus=event_bus,
            agent_library=agent_library,
        ),
        agent_library=agent_library,
        user_input=user_input,
        todo_cleanup=TodoCleanupStub(),
        llm_provider=llm_provider,
        project_tree=DummyProjectTree(),
        event_store=NoOpEventStore(),
        agent_task_manager=AgentTaskManager(),
    )

    await session.run_async(create_session_args(False, start_message="Start"))

    responses = [
        event.response for event in event_spy.get_events(AssistantRespondedEvent)
    ]
    assert "Response from new-model" in responses
