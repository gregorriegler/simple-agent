from unittest.mock import patch, Mock

from approvaltests import verify, Options

from main import run_session, SessionArgs
from application.chat import Messages
from infrastructure.console_display import ConsoleDisplay
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
    verify_chat(enter, "Hello", "Hello! How can I help you?")


def test_chat_with_two_regular_responses():
    verify_chat(lambda _ : "User Answer", "Hello", ["Answer 1", "Answer 2"], 2)


def test_abort():
    verify_chat(keyboard_interrupt, "Test message", "Test answer")


def test_tool_cat(tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    verify_chat(enter, "Test message", f"🛠️ cat {temp_file}")


def test_tool_cat_integration(tmp_path):
    temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
    verify_chat(enter, "Test message", f"🛠️ cat {temp_file}")


def test_tool_ls_integration(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    verify_chat(enter, "Test message", f"🛠️ ls {directory_path}")


def test_chat_with_task_completion():
    verify_chat(enter, "Say Hello", [
        "Hello!",
        "🛠️ complete-task I successfully said hello", "ignored"
    ], rounds=3)


def test_subagent():
    verify_chat(enter, "Create a subagent that says hello", [
        "🛠️ subagent say hello", "hello",
        "🛠️ complete-task I successfully said hello"
    ])


def test_nested_agent_test():
    verify_chat(enter, "Create a subagent that creates another subagent", [
        "🛠️ subagent create another subagent",
        "🛠️ subagent say nested hello",
        "nested hello",
        "🛠️ complete-task I successfully said nested hello",
        "🛠️ complete-task I successfully created another subagent"
    ])


def test_agent_says_after_subagent():
    verify_chat(enter, "Create a subagent that says hello, then say goodbye", [
        "🛠️ subagent say hello",
        "hello",
        "🛠️ complete-task I successfully said hello",
        "goodbye"
    ], rounds=2)


@patch('tools.bash_tool.subprocess.run')
def test_tool_bash(mock_subprocess):
    mock_result = Mock()
    mock_result.stdout = "hello"
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_subprocess.return_value = mock_result

    verify_chat(enter, "use bash", f"🛠️ bash echo hello")


def create_chat_stub(answer):
    if isinstance(answer, list):
        answer_index = 0

        def chat_stub(system_prompt=None, messages=None):
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


def verify_chat(input_stub, message, answer, rounds=1):
    chat_stub = create_chat_stub(answer)
    result = run_chat_test(input_stub, message, chat_stub, rounds)
    verify(result, options=Options().with_scrubber(all_scrubbers()))


def run_chat_test(input_stub, message, chat_stub, rounds=1):
    saved_messages = "None"

    def save_messages(messages):
        nonlocal saved_messages
        saved_messages = "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)

    def load_messages():
        return Messages()

    print_spy = PrintSpy()
    display = ConsoleDisplay(print_fn=print_spy)

    class TestToolLibrary(ToolLibrary):
        def __init__(self, chat):
            super().__init__(chat, print_fn=print_spy)

    class TestSystemPromptGenerator:
        def generate_system_prompt(self):
            return "Test system prompt"

    args = SessionArgs(False, message)

    with patch('builtins.input', input_stub):
        with patch('main.ToolLibrary', TestToolLibrary):
            with patch('main.SystemPromptGenerator', TestSystemPromptGenerator):
                run_session(args, display, load_messages, save_messages, chat_stub, rounds)

    return f"# Standard out:\n{print_spy.get_output()}\n\n# Saved messages:\n{saved_messages}"
