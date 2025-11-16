from approvaltests import verify

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AssistantRespondedEvent,
    AssistantSaidEvent,
    AgentCreatedEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.application.input import Input
from simple_agent.application.app_context import AppContext
from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.application.session import run_session
from simple_agent.application.todo_cleanup import NoOpTodoCleanup
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from .event_spy import EventSpy
from .fake_display import FakeDisplay
from .print_spy import IOSpy
from .system_prompt_generator_test import GroundRulesStub
from .test_helpers import create_test_prompt, create_session_args
from .test_session_storage import SessionStorageStub
from .test_tool_library import ToolLibraryStub


def test_subagent():
    verify_chat(
        ["Create a subagent that says hello", "\n"], [
            "🛠️ subagent coding say hello",
            "hello\n🛠️ complete-task I successfully said hello"
        ]
    )


def test_nested_agent_test():
    verify_chat(
        ["Create a subagent that creates another subagent", "\n"], [
            "🛠️ subagent orchestrator create another subagent",
            "🛠️ subagent coding say nested hello",
            "nested hello\n🛠️ complete-task I successfully said nested hello",
            "🛠️ complete-task I successfully created another subagent",
            "🛠️ complete-task I successfully created a subagent"
        ]
    )


def test_agent_says_after_subagent():
    verify_chat(
        ["Create a subagent that says hello, then say goodbye", "\n"], [
            "🛠️ subagent coding say hello",
            "hello\n🛠️ complete-task I successfully said hello",
            "goodbye"
        ]
    )


def verify_chat(inputs, answers, escape_hits=None, ctrl_c_hits=None):
    llm_stub = create_llm_stub(answers)
    message, *remaining_inputs = inputs
    io_spy = IOSpy(remaining_inputs, escape_hits)
    user_input_port = ConsoleUserInput(0, io=io_spy)
    user_input = Input(user_input_port)
    user_input.stack(message)
    test_session_storage = SessionStorageStub()
    event_bus = SimpleEventBus()
    display = FakeDisplay()

    event_spy = EventSpy()
    tracked_events = [
        SessionStartedEvent,
        UserPromptRequestedEvent,
        UserPromptedEvent,
        AssistantSaidEvent,
        AssistantRespondedEvent,
        ToolCalledEvent,
        ToolResultEvent,
        SessionInterruptedEvent,
        SessionEndedEvent,
    ]

    for event_type in tracked_events:
        event_bus.subscribe(event_type, event_spy.record_event)

    event_bus.subscribe(AssistantSaidEvent, display.assistant_says)
    event_bus.subscribe(ToolCalledEvent, display.tool_call)
    event_bus.subscribe(ToolResultEvent, display.tool_result)
    event_bus.subscribe(SessionStartedEvent, display.start_session)
    event_bus.subscribe(SessionInterruptedEvent, display.interrupted)
    event_bus.subscribe(SessionEndedEvent, display.exit)
    event_bus.subscribe(AgentCreatedEvent, display.agent_created)

    test_tool_library = ToolLibraryStub(
        llm_stub,
        io=io_spy,
        interrupts=[ctrl_c_hits],
        event_bus=event_bus,
        all_displays=display
    )

    agent_library = BuiltinAgentLibrary()
    app_context = AppContext(
        llm=llm_stub,
        event_bus=event_bus,
        session_storage=test_session_storage,
        tool_library_factory=None,
        agent_library=agent_library,
        create_subagent_input=lambda indent: user_input
    )

    run_session(
        create_session_args(False),
        app_context,
        "Agent",
        NoOpTodoCleanup(),
        test_tool_library,
        user_input,
        create_test_agent_definition()
    )

    result = f"# Events\n{event_spy.get_events_as_string()}\n\n# Saved messages:\n{test_session_storage.saved}"
    verify(result)

def create_test_agent_definition():
    return AgentDefinition(
        "Agent", """---
name: Agent
---""",
        GroundRulesStub("Test system prompt")
    )



