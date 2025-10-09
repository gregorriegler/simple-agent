from approvaltests import verify, Options

from simple_agent.application.input import Input
from simple_agent.application.session import run_session
from simple_agent.infrastructure.console_display import ConsoleDisplay
from simple_agent.infrastructure.console_user_input import ConsoleUserInput
from .print_spy import IOSpy
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure, all_scrubbers
)
from .test_session_storage import TestSessionStorage
from .test_tool_library import TestToolLibrary


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
    verify_chat(["Say Hello", "\n"], [
        "Hello!\n🛠️ complete-task I successfully said hello",
        "ignored"
    ])


def test_subagent():
    verify_chat(["Create a subagent that says hello", "\n"], [
        "🛠️ subagent say hello",
        "hello\n🛠️ complete-task I successfully said hello"
    ])


def test_nested_agent_test():
    verify_chat(["Create a subagent that creates another subagent", "\n"], [
        "🛠️ subagent create another subagent",
        "🛠️ subagent say nested hello",
        "nested hello\n🛠️ complete-task I successfully said nested hello",
        "🛠️ complete-task I successfully created another subagent",
        "🛠️ complete-task I successfully created a subagent"
    ])


def test_agent_says_after_subagent():
    verify_chat(["Create a subagent that says hello, then say goodbye", "\n"], [
        "🛠️ subagent say hello",
        "hello\n🛠️ complete-task I successfully said hello",
        "goodbye"
    ])


def test_escape_reads_follow_up_message():
    verify_chat(["Hello", "Follow-up message", "\n"], "Assistant response", [True, False])


def test_escape_aborts_tool_call():
    verify_chat(["Hello", "Follow-up message", "\n"], ["🛠️ cat hello.txt", "🛠️ complete-task summary"], [True, False])


def test_interrupt_reads_follow_up_message():
    verify_chat(["Hello", "Follow-up message", "\n"], "Assistant response", [], [True, False])


def test_interrupt_aborts_tool_call():
    verify_chat(["Hello", "Follow-up message", "\n"], ["🛠️ cat hello.txt", "🛠️ complete-task summary"], [], [True, False])


def verify_chat(inputs, answers, escape_hits=None, ctrl_c_hits=None):
    llm_stub = create_llm_stub(answers)
    message, *remaining_inputs = inputs
    io_spy = IOSpy(remaining_inputs, escape_hits)
    display = ConsoleDisplay(io=io_spy)
    user_input_port = ConsoleUserInput(display.indent_level, io=io_spy)
    user_input = Input(user_input_port)
    user_input.stack(message)
    test_session_storage = TestSessionStorage()
    test_tool_library = TestToolLibrary(llm_stub, io=io_spy, interrupts=[ctrl_c_hits])

    run_session(False, user_input, display, test_session_storage, llm_stub, system_prompt_stub, test_tool_library)

    result = f"# Standard out:\n{io_spy.get_output()}\n\n# Saved messages:\n{test_session_storage.saved}"
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
