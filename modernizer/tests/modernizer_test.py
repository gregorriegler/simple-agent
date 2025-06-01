import builtins
import os
import re
import sys
import pytest
from approvaltests import verify, verify_as_json
from approvaltests.reporters.report_with_beyond_compare import ReportWithWinMerge
from approvaltests import set_default_reporter
from approvaltests.scrubbers import create_regex_scrubber
from approvaltests import Options
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modernizer.modernizer import start_chat

@pytest.fixture(scope="session", autouse=True)
def set_default_reporter_for_all_tests() -> None:
    set_default_reporter(ReportWithWinMerge())

def create_temp_file(tmp_path, filename, contents):
    temp_file = tmp_path / filename
    temp_file.write_text(contents)
    return temp_file

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
    
    temp_path_scrubber = create_regex_scrubber('/cat.*', '/cat /tmp/path/testfile.txt')
    verify(result, options=Options().with_scrubber(temp_path_scrubber))