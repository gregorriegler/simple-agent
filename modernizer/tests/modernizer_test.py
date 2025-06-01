import builtins
import os
import sys
import pytest
from approvaltests import verify
from approvaltests.reporters.report_with_beyond_compare import ReportWithWinMerge
from approvaltests import set_default_reporter
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modernizer.modernizer import start_chat

@pytest.fixture(scope="session", autouse=True)
def set_default_reporter_for_all_tests() -> None:
    set_default_reporter(ReportWithWinMerge())

def create_input_stub():
    call_count = 0
    def input_stub(_):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "\n"
        raise KeyboardInterrupt()
    return input_stub

def run_chat_test(capsys, message, answer):
    builtins.input = create_input_stub()
    claude_stub = lambda messages, system_prompt: answer
    
    try:
        start_chat(message, new=True, message_claude=claude_stub)
    except KeyboardInterrupt:
        pass
        
    captured = capsys.readouterr()
    return captured.out

def test_start_chat_with_new_session(capsys):
    result = run_chat_test(capsys, "Test message", "Test answer")
    verify(result)