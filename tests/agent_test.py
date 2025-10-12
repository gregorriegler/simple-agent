from approvaltests import verify, Options

from simple_agent.application.input import Input
from simple_agent.application.session import run_session
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import EventType
from simple_agent.infrastructure.console_display import ConsoleDisplay
from simple_agent.infrastructure.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.display_event_handler import DisplayEventHandler
from .event_spy import EventSpy
from .print_spy import IOSpy
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure, all_scrubbers
)
from .test_session_storage import SessionStorageStub
from .test_tool_library import ToolLibraryStub


def test_chat_with_regular_response():
    verify_chat(["Hello", "\n"], "Hello! How can I help you?")


def test_chat_with_two_regular_responses():
    verify_chat(["Hello", "User Answer", "\n"], ["Answer 1", "Answer 2"])


def test_chat_with_empty_answer():
    verify_chat(["Hello", ""], "Test answer")


def test_abort():
    verify_chat(["Test message", keyboard_interrupt], "Test answer")


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


def test_subagent():
    verify_chat(
        ["Create a subagent that says hello", "\n"], [
            "🛠️ subagent say hello",
            "hello\n🛠️ complete-task I successfully said hello"
        ]
    )


def test_nested_agent_test():
    verify_chat(
        ["Create a subagent that creates another subagent", "\n"], [
            "🛠️ subagent create another subagent",
            "🛠️ subagent say nested hello",
            "nested hello\n🛠️ complete-task I successfully said nested hello",
            "🛠️ complete-task I successfully created another subagent",
            "🛠️ complete-task I successfully created a subagent"
        ]
    )


def test_agent_says_after_subagent():
    verify_chat(
        ["Create a subagent that says hello, then say goodbye", "\n"], [
            "🛠️ subagent say hello",
            "hello\n🛠️ complete-task I successfully said hello",
            "goodbye"
        ]
    )


def test_escape_reads_follow_up_message():
    verify_chat(["Hello", "Follow-up message", "\n"], "Assistant response", [True, False])


def test_escape_aborts_tool_call():
    verify_chat(["Hello", "Follow-up message", "\n"], ["🛠️ cat hello.txt", "🛠️ complete-task summary"], [True, False])


def test_interrupt_reads_follow_up_message():
    verify_chat(["Hello", "Follow-up message", "\n"], "Assistant response", [], [True, False])


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
    display_handler = DisplayEventHandler(display)

    event_spy = EventSpy()
    for event_type in EventType:
        event_bus.subscribe(event_type, lambda event_data, et=event_type: event_spy.record_event(et, event_data))

    event_bus.subscribe(EventType.ASSISTANT_SAID, display_handler.handle_assistant_said)
    event_bus.subscribe(EventType.TOOL_CALLED, display_handler.handle_tool_called)
    event_bus.subscribe(EventType.TOOL_RESULT, display_handler.handle_tool_result)
    event_bus.subscribe(EventType.SESSION_STARTED, display_handler.handle_session_started)
    event_bus.subscribe(EventType.SESSION_ENDED, display_handler.handle_session_ended)

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
        system_prompt_stub,
        user_input,
        llm_stub,
        test_tool_library,
        test_session_storage,
        event_bus
    )

    result = f"# Events\n{event_spy.get_events_as_string()}\n\n# Saved messages:\n{test_session_storage.saved}"
    verify(result, options=Options().with_scrubber(all_scrubbers()))


def create_llm_stub(answer):
    if isinstance(answer, list):
        answer_index = 0

        def llm_stub(system_prompt, messages):
            nonlocal answer_index
            if answer_index < len(answer):
                result = answer[answer_index]
                answer_index += 1
                return result
            if answer:
                return answer[-1]
            return ""

        return llm_stub

    def llm_answer(system_prompt, messages):
        return answer

    return llm_answer


def enter(_):
    return "\n"


def keyboard_interrupt(_):
    raise KeyboardInterrupt()


def system_prompt_stub(tool_library):
    return "Test system prompt"
