from unittest.mock import patch

from approvaltests import verify, Options

from application.chat import Messages
from infrastructure.console_display import ConsoleDisplay
from main import run_session, SessionArgs
from tools import ToolLibrary
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure, all_scrubbers
)


class PrintSpy:
    def __init__(self):
        self.captured_output = []

    def __call__(self, *args, **kwargs):
        if args:
            message = ' '.join(str(arg) for arg in args)
        else:
            message = ''

        self.captured_output.append(message)

    def get_output(self):
        return '\n'.join(self.captured_output)


def enter(_):
    return "\n"


def keyboard_interrupt(_):
    raise KeyboardInterrupt()


def test_chat_with_regular_response():
    verify_chat("Hello", enter, "Hello! How can I help you?")


def test_chat_with_two_regular_responses():
    verify_chat("Hello", lambda _: "User Answer", ["Answer 1", "Answer 2"], 2)


def test_chat_with_empty_answer():
    verify_chat("Hello", lambda _ : "", "Test answer", 2)


def test_abort():
    verify_chat("Test message", keyboard_interrupt, "Test answer")


def test_tool_cat(tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    verify_chat("Test message", enter, f"🛠️ cat {temp_file}")


def test_tool_cat_integration(tmp_path):
    temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
    verify_chat("Test message", enter, f"🛠️ cat {temp_file}")


def test_tool_ls_integration(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    verify_chat("Test message", enter, f"🛠️ ls {directory_path}")


def test_chat_with_task_completion():
    verify_chat("Say Hello", enter, [
        "Hello!\n🛠️ complete-task I successfully said hello",
        "ignored"
    ], rounds=2)


def test_subagent():
    verify_chat("Create a subagent that says hello", enter, [
        "🛠️ subagent say hello", "hello\n🛠️ complete-task I successfully said hello"
    ])


def test_nested_agent_test():
    verify_chat("Create a subagent that creates another subagent", enter, [
        "🛠️ subagent create another subagent",
        "🛠️ subagent say nested hello",
        "nested hello\n🛠️ complete-task I successfully said nested hello",
        "🛠️ complete-task I successfully created another subagent"
    ])


def test_agent_says_after_subagent():
    verify_chat("Create a subagent that says hello, then say goodbye", enter, [
        "🛠️ subagent say hello",
        "hello\n🛠️ complete-task I successfully said hello",
        "goodbye"
    ], rounds=2)


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


def verify_chat(message, input_stub, answer, rounds=1):
    chat_stub = create_chat_stub(answer)
    result = run_chat_test(input_stub, message, chat_stub, rounds)
    verify(result, options=Options().with_scrubber(all_scrubbers()))


def run_chat_test(input_stub, message, chat_stub, rounds=1):
    class TestSessionStorage:
        def __init__(self):
            self.saved = "None"

        def load(self):
            return Messages()

        def save(self, messages):
            self.saved = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)

    print_spy = PrintSpy()
    display = ConsoleDisplay(print_fn=print_spy)

    class TestToolLibrary(ToolLibrary):
        def __init__(self, chat):
            super().__init__(chat, print_fn=print_spy)

    class TestSystemPromptGenerator:
        def generate_system_prompt(self):
            return "Test system prompt"

    args = SessionArgs(False, message)

    test_session_storage = TestSessionStorage()

    with patch('builtins.input', input_stub):
        with patch('main.ToolLibrary', TestToolLibrary):
            with patch('main.SystemPromptGenerator', TestSystemPromptGenerator):
                run_session(args, display, test_session_storage, chat_stub, rounds)

    return f"# Standard out:\n{print_spy.get_output()}\n\n# Saved messages:\n{test_session_storage.saved}"
