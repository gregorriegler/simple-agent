import builtins
from approvaltests import verify, Options

from agent import start_chat
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure,
    multi_scrubber
)

def enter(_):
    return "\n"

def keyboard_interrupt(_):
    raise KeyboardInterrupt()

def run_chat_test(capsys, input_stub, message, answer):
    builtins.input = input_stub
    claude_stub = lambda messages, system_prompt: answer

    saved_messages = "None"
    def save_chat(chat):
        nonlocal saved_messages
        saved_messages = "\n".join(f"{msg['role']}: {msg['content']}" for msg in chat)

    # Mock system prompt for tests
    system_prompt = "Test system prompt"

    try:
        start_chat(system_prompt, message, new=True, message_claude=claude_stub, rounds=1, save_chat=save_chat)
    except KeyboardInterrupt:
        pass

    captured = capsys.readouterr()
    return f"# Standard out:\n{captured.out}\n\n# Saved messages:\n{saved_messages}"

def test_start_chat_with_new_session(capsys):
    verify_chat(capsys, enter, "Test message", "Test answer")

def test_abort(capsys):
    verify_chat(capsys, keyboard_interrupt, "Test message", "Test answer")

def test_tool_cat(capsys, tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    verify_chat(capsys, enter, "Test message", f"/cat {temp_file}")

def test_tool_cat_integration(capsys, tmp_path):
    temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
    verify_chat(capsys, enter, "Test message", f"/cat {temp_file}")

def test_tool_ls_integration(capsys, tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    verify_chat(capsys, enter, "Test message", f"/ls {directory_path}")

def test_chat_with_regular_response(capsys):
    verify_chat(capsys, enter, "Hello", "Hello! How can I help you?")

def verify_chat(capsys, input_stub, message, answer):
    result = run_chat_test(capsys, input_stub=input_stub, message=message, answer=answer)
    verify(result, options=Options().with_scrubber(multi_scrubber))

