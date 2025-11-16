from approvaltests import verify, Options

from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AssistantRespondedEvent,
    AssistantSaidEvent,
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
from .event_spy import EventSpy
from .print_spy import IOSpy
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure, all_scrubbers
)
from .test_session_storage import SessionStorageStub
from .test_tool_library import ToolLibraryStub


def test_chat_with_regular_response():
    verify_chat(["Hello", "\n"], ["Hello! How can I help you?"])


def test_chat_with_two_regular_responses():
    verify_chat(["Hello", "User Answer", "\n"], ["Answer 1", "Answer 2"])


def test_chat_with_empty_answer():
    verify_chat(["Hello", ""], ["Test answer"])


def test_abort():
    verify_chat(["Test message", keyboard_interrupt], ["Test answer"])


def test_tool_cat(tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    verify_chat(["Test message", "\n"], [f"🛠️ cat {temp_file}", "🛠️ complete-task summary"])


def test_tool_cat_integration(tmp_path):
    temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
    verify_chat(["Test message", "\n"], [f"🛠️ cat {temp_file}", "🛠️ complete-task summary"])


def test_tool_ls_integration(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    verify_chat(["Test message", "\n"], [f"🛠️ ls {directory_path}", "🛠️ complete-task summary"])


def test_chat_with_task_completion():
    verify_chat(
        ["Say Hello", "\n"], [
            "Hello!\n🛠️ complete-task I successfully said hello",
            "ignored"
        ]
    )


def test_escape_reads_follow_up_message():
    verify_chat(["Hello", "Follow-up message", "\n"], ["Assistant response"], [True, False])


def test_escape_aborts_tool_call():
    verify_chat(["Hello", "Follow-up message", "\n"], ["🛠️ cat hello.txt", "🛠️ complete-task summary"], [True, False])


def test_interrupt_reads_follow_up_message():
    verify_chat(["Hello", "Follow-up message", "\n"], ["Assistant response"], [], [True, False])


def test_interrupt_aborts_tool_call():
    verify_chat(
        ["Hello", "Follow-up message", "\n"], ["🛠️ cat hello.txt", "🛠️ complete-task summary"], [], [True, False]
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
    display_handler = AllDisplays()
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

    test_tool_library = ToolLibraryStub(
        llm_stub,
        io=io_spy,
        interrupts=[ctrl_c_hits],
        event_bus=event_bus,
        display_event_handler=display_handler
    )
    run_session(
        False,
        "Agent",
        "Test system prompt",
        user_input,
        llm_stub,
        test_tool_library,
        test_session_storage,
        event_bus,
        NoOpTodoCleanup()
    )

    result = f"# Events\n{event_spy.get_events_as_string()}\n\n# Saved messages:\n{test_session_storage.saved}"
    verify(result, options=Options().with_scrubber(all_scrubbers()))


def enter(_):
    return "\n"


def keyboard_interrupt(_):
    raise KeyboardInterrupt()
