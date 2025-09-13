import builtins
import platform
from unittest.mock import patch, Mock
from approvaltests import verify, Options

from agent import Agent
from chat import Chat
from console_display import ConsoleDisplay
from tools import ToolLibrary
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure, all_scrubbers
)


def enter(_):
    return "\n"


def keyboard_interrupt(_):
    raise KeyboardInterrupt()


def test_chat_with_regular_response(capsys):
    verify_chat(capsys, enter, "Hello", "Hello! How can I help you?")


def test_chat_with_two_regular_responses(capsys):
    verify_chat(capsys, lambda _ : "User Answer", "Hello", ["Answer 1", "Answer 2"], 2)


def test_abort(capsys):
    verify_chat(capsys, keyboard_interrupt, "Test message", "Test answer")


def test_tool_cat(capsys, tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    verify_chat(capsys, enter, "Test message", f"🛠️ cat {temp_file}")


def test_tool_cat_integration(capsys, tmp_path):
    temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
    verify_chat(capsys, enter, "Test message", f"🛠️ cat {temp_file}")


def test_tool_ls_integration(capsys, tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    verify_chat(capsys, enter, "Test message", f"🛠️ ls {directory_path}")


def test_chat_with_task_completion(capsys):
    verify_chat(capsys, enter, "Say Hello", ["Hello!", "🛠️ complete-task I successfully said hello", "ignored"], rounds=3)


def test_subagent(capsys):
    verify_chat(capsys, enter, "Create a subagent that says hello", ["🛠️ subagent say hello", "hello", "🛠️ complete-task I successfully said hello"])


def test_nested_agent_test(capsys):
    verify_chat(capsys, enter, "Create a subagent that creates another subagent", [
        "🛠️ subagent create another subagent",
        "🛠️ subagent say nested hello",
        "nested hello",
        "🛠️ complete-task I successfully said nested hello",
        "🛠️ complete-task I successfully created another subagent"
    ])


def test_agent_says_after_subagent(capsys):
    verify_chat(capsys, enter, "Create a subagent that says hello, then say goodbye", [
        "🛠️ subagent say hello",
        "hello",
        "🛠️ complete-task I successfully said hello",
        "goodbye"
    ], rounds=2)


@patch('tools.bash_tool.subprocess.run')
def test_tool_bash(mock_subprocess, capsys):
    mock_result = Mock()
    mock_result.stdout = "hello"
    mock_result.stderr = ""
    mock_result.returncode = 0
    mock_subprocess.return_value = mock_result

    verify_chat(capsys, enter, "use bash", f"🛠️ bash echo hello")


def create_claude_stub(answer):
    if isinstance(answer, list):
        answer_index = 0

        def claude_stub(messages, system_prompt):
            nonlocal answer_index
            if answer_index < len(answer):
                result = answer[answer_index]
                answer_index += 1
                return result
            else:
                return answer[-1] if answer else ""
        return claude_stub
    else:
        return lambda messages, system_prompt: answer


def verify_chat(capsys, input_stub, message, answer, rounds=1):
    claude_stub = create_claude_stub(answer)
    result = run_chat_test(capsys, input_stub, message, claude_stub, rounds)
    verify(result, options=Options().with_scrubber(all_scrubbers()))


def run_chat_test(capsys, input_stub, message, claude_stub, rounds=1):
    builtins.input = input_stub

    saved_messages = "None"

    def save_chat(chat):
        nonlocal saved_messages
        saved_messages = "\n".join(f"{msg['role']}: {msg['content']}" for msg in chat)

    system_prompt = "Test system prompt"

    chat = Chat()
    print("Starting new session")

    if message:
        chat.user_says(message)

    try:
        agent = Agent(system_prompt, claude_stub, ConsoleDisplay(), ToolLibrary(claude_stub), save_chat)
        agent.start(chat, rounds)
    except KeyboardInterrupt:
        pass

    captured = capsys.readouterr()
    return f"# Standard out:\n{captured.out}\n\n# Saved messages:\n{saved_messages}"
