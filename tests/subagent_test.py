from approvaltests import verify

from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AssistantRespondedEvent,
    AssistantSaidEvent,
    SubagentCreatedEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.application.input import Input
from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.application.session import run_session
from simple_agent.application.todo_cleanup import NoOpTodoCleanup
from simple_agent.infrastructure.console.console_display import ConsoleDisplay
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.display_event_handler import AllDisplays
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from .event_spy import EventSpy
from .print_spy import IOSpy
from .test_session_storage import SessionStorageStub
from .test_tool_library import ToolLibraryStub
from .test_helpers import create_test_prompt, create_session_args


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
    display = ConsoleDisplay(0, "Agent", io_spy)
    user_input_port = ConsoleUserInput(display.indent_level, io=io_spy)
    user_input = Input(user_input_port)
    user_input.stack(message)
    test_session_storage = SessionStorageStub()
    event_bus = SimpleEventBus()
    display_factory = lambda agent_id, agent_name, indent: ConsoleDisplay(indent, agent_name or agent_id, io_spy)
    display_handler = AllDisplays(display_factory=display_factory)
    display_handler.register_display("Agent", display)

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

    event_bus.subscribe(AssistantSaidEvent, display_handler.assistant_says)
    event_bus.subscribe(ToolCalledEvent, display_handler.tool_call)
    event_bus.subscribe(ToolResultEvent, display_handler.tool_result)
    event_bus.subscribe(SessionStartedEvent, display_handler.start_session)
    event_bus.subscribe(SessionInterruptedEvent, display_handler.interrupted)
    event_bus.subscribe(SessionEndedEvent, display_handler.exit)
    event_bus.subscribe(SubagentCreatedEvent, display_handler.subagent_created)

    test_tool_library = ToolLibraryStub(
        llm_stub,
        io=io_spy,
        interrupts=[ctrl_c_hits],
        event_bus=event_bus,
        all_displays=display_handler
    )

    prompt = create_test_prompt()
    run_session(
        create_session_args(False),
        BuiltinAgentLibrary(),
        display,
        event_bus,
        llm_stub,
        prompt,
        test_session_storage,
        "Agent",
        NoOpTodoCleanup(),
        test_tool_library,
        user_input
    )

    result = f"# Events\n{event_spy.get_events_as_string()}\n\n# Saved messages:\n{test_session_storage.saved}"
    verify(result)



