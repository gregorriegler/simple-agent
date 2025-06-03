import builtins
import os
import sys
import pytest
from approvaltests import verify, verify_as_json
from approvaltests import Options
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modernizer.modernizer import start_chat
from .test_helpers import (
    set_default_reporter_for_all_tests,
    create_temp_file,
    create_temp_directory_structure,
    create_path_scrubber,
    create_date_scrubber,
    create_multi_scrubber
)

def enter(_):
    return "\n"

def keyboard_interrupt(_):
    raise KeyboardInterrupt()
    
def run_chat_test(capsys, input_stub, message, answer):
    builtins.input = input_stub
    claude_stub = lambda messages, system_prompt: answer

    saved_messages = "None"
    def save_session(messages):
        nonlocal saved_messages
        saved_messages = "\n".join(str(msg['role'] + ": " + msg['content']) for msg in messages)
    
    try:
        start_chat(message, new=True, message_claude=claude_stub, rounds=1, save_session=save_session)
    except KeyboardInterrupt:
        pass
        
    captured = capsys.readouterr()
    return f"""# Standard out:
{captured.out}

# Saved messages:
{saved_messages}"""

def test_start_chat_with_new_session(capsys):
    result = run_chat_test(capsys, input_stub=enter, message="Test message", answer="Test answer")
    verify(result)

def test_abort(capsys):
    result = run_chat_test(capsys, input_stub=keyboard_interrupt, message="Test message", answer="Test answer")
    verify(result)

def test_tool_cat(capsys, tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    
    result = run_chat_test(capsys, input_stub=enter, message="Test message", answer=f"/cat {temp_file}")
    
    path_scrubber = create_path_scrubber(temp_file, '/tmp/path/testfile.txt')
    verify(result, options=Options().with_scrubber(path_scrubber))


def test_tool_ls_integration(capsys, tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    result = run_chat_test(capsys, input_stub=enter, message="Test message", answer=f"/ls {directory_path}")
    
    path_scrubber = create_path_scrubber(directory_path)
    multi_scrubber = create_multi_scrubber(path_scrubber)
    
    verify(result, options=Options().with_scrubber(multi_scrubber))

def test_tool_cat_integration(capsys, tmp_path):
    temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
    result = run_chat_test(capsys, input_stub=enter, message="Test message", answer=f"/cat {temp_file}")
    
    path_scrubber = create_path_scrubber(temp_file, '/tmp/test_path/integration_test.txt')
    verify(result, options=Options().with_scrubber(path_scrubber))

def test_multiple_tool_calls_integration(capsys, tmp_path):
    temp_file = create_temp_file(tmp_path, "multi_test.txt", "Multi-tool test")
    ls_result = run_chat_test(capsys, input_stub=enter, message="Test message", answer=f"/ls {tmp_path}")
    cat_result = run_chat_test(capsys, input_stub=enter, message="Test message", answer=f"/cat {temp_file}")
    
    combined_result = f"=== LS RESULT ===\n{ls_result}\n\n=== CAT RESULT ===\n{cat_result}"
    path_scrubber = create_path_scrubber(tmp_path)
    multi_scrubber = create_multi_scrubber(path_scrubber)
    
    verify(combined_result, options=Options().with_scrubber(multi_scrubber))

def test_chat_with_regular_response(capsys):
    result = run_chat_test(capsys, input_stub=enter, message="Hello", answer="Hello! How can I help you?")
    verify(result)
