from unittest.mock import patch

from approvaltests import verify, Options

from application.input import Input
from infrastructure.console_display import ConsoleDisplay
from application.session import run_session, SessionArgs
from tools import ToolLibrary
from .print_spy import PrintSpy
from .test_console_escape_detector import TestConsoleEscapeDetector
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure, all_scrubbers
)
from .test_session_storage import TestSessionStorage


def enter(_):
    return "\n"


def keyboard_interrupt(_):
    raise KeyboardInterrupt()


def test_chat_with_regular_response():
    verify_chat("Hello", "\n", "Hello! How can I help you?", 2)


def test_chat_with_two_regular_responses():
    verify_chat("Hello", ["User Answer", "\n"], ["Answer 1", "Answer 2"], 3)


def test_chat_with_empty_answer():
    verify_chat("Hello", "", "Test answer", 2)


def test_abort():
    verify_chat("Test message", [keyboard_interrupt], "Test answer", 2)


def test_tool_cat(tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    verify_chat("Test message", "\n", f"🛠️ cat {temp_file}", 2)


def test_tool_cat_integration(tmp_path):
    temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
    verify_chat("Test message", "\n", f"🛠️ cat {temp_file}", 2)


def test_tool_ls_integration(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    verify_chat("Test message", "\n", f"🛠️ ls {directory_path}", 2)


def test_chat_with_task_completion():
    verify_chat("Say Hello", "\n", [
        "Hello!\n🛠️ complete-task I successfully said hello",
        "ignored"
    ], rounds=2)


def test_subagent():
    verify_chat("Create a subagent that says hello", "\n", [
        "🛠️ subagent say hello",
        "hello\n🛠️ complete-task I successfully said hello",
        ""
    ], 2)


def test_nested_agent_test():
    verify_chat("Create a subagent that creates another subagent", "\n", [
        "🛠️ subagent create another subagent",
        "🛠️ subagent say nested hello",
        "nested hello\n🛠️ complete-task I successfully said nested hello",
        "🛠️ complete-task I successfully created another subagent",
        ""
    ], 2)


def test_agent_says_after_subagent():
    verify_chat("Create a subagent that says hello, then say goodbye", "\n", [
        "🛠️ subagent say hello",
        "hello\n🛠️ complete-task I successfully said hello",
        "goodbye"
    ], rounds=3)


def test_escape_reads_follow_up_message():
    detector = create_escape_detector_stub([True, False])
    verify_chat("Hello", ["Follow-up message", "\n"], "Assistant response", 1, detector)


def create_escape_detector_stub(values):
    if isinstance(values, list):
        index = 0

        def detector():
            nonlocal index
            if index < len(values):
                result = values[index]
                index += 1
                return result
            return values[-1] if values else False

        return detector
    return lambda: bool(values)


def create_chat_stub(answer):
    if isinstance(answer, list):
        answer_index = 0

        def chat_stub(system_prompt, messages):
            nonlocal answer_index
            if answer_index < len(answer):
                result = answer[answer_index]
                answer_index += 1
                return result
            if answer:
                return answer[-1]
            return ""

        return chat_stub

    def single_chat_stub(system_prompt, messages):
        return answer

    return single_chat_stub


def create_input_stub(inputs):
    if isinstance(inputs, str):
        return lambda _: inputs
    if isinstance(inputs, list):
        input_index = 0

        def input_stub(_):
            nonlocal input_index
            if input_index < len(inputs):
                result = inputs[input_index]
                input_index += 1
                if isinstance(result, str):
                    return result
                return result(_)
            return ""

        return input_stub
    return input


def verify_chat(message, input_stub, answer, rounds=1, escape_detector=None):
    chat_stub = create_chat_stub(answer)
    input_stub = create_input_stub(input_stub)
    result = run_chat_test(input_stub, message, chat_stub, rounds, escape_detector)
    verify(result, options=Options().with_scrubber(all_scrubbers()))


def run_chat_test(input_stub, message, chat_stub, rounds=1, escape_detector=None):

    class TestToolLibrary(ToolLibrary):
        def __init__(self, chat):
            super().__init__(chat, print_fn=print_spy)

    detector = escape_detector or create_escape_detector_stub(False)

    print_spy = PrintSpy()

    display = ConsoleDisplay(print_fn=print_spy)

    def test_system_prompt():
        return "Test system prompt"

    args = SessionArgs(False, message)

    test_session_storage = TestSessionStorage()

    user_input = Input(display, detector)
    user_input.stack(args.start_message)

    with patch('builtins.input', input_stub):
        with patch('application.session.ToolLibrary', TestToolLibrary):
            with patch('tools.subagent_tool.ConsoleEscapeDetector', TestConsoleEscapeDetector):
                run_session(args, user_input, display, test_session_storage, chat_stub, test_system_prompt, rounds)

    return f"# Standard out:\n{print_spy.get_output()}\n\n# Saved messages:\n{test_session_storage.saved}"
