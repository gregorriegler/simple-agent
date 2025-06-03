import builtins
import os
import re
import sys
import pytest
from approvaltests import verify, verify_as_json
from approvaltests.reporters.report_with_beyond_compare import ReportWithWinMerge
from approvaltests import set_default_reporter
from approvaltests.scrubbers import create_regex_scrubber, combine_scrubbers
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

def create_temp_directory_structure(tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.write_text("Hello world\nLine 2\nLine 3")
    
    file2 = tmp_path / "file2.py"
    file2.write_text("def hello():\n    print('Hello')\n    return 42")
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subfile = subdir / "subfile.txt"
    subfile.write_text("Subdirectory file content")
    
    return tmp_path, file1, file2, subdir, subfile

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

class TestModernizerIntegration:
    def enter_input(_, prompt=""):
        return "\n"

    def keyboard_interrupt(_):
        raise KeyboardInterrupt()
    
    def run_chat_test(self, capsys, input_stub, message, answer):
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

    def test_tool_ls_integration(self, capsys, tmp_path):
        directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
        result = self.run_chat_test(capsys, input_stub=self.enter_input, message="Test message", answer=f"/ls {directory_path}")
        
        temp_path_scrubber = create_regex_scrubber(str(directory_path).replace('\\', '\\\\'), '/tmp/test_path')
        date_scrubber = create_regex_scrubber(r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', '[DATE]')
        multi_scrubber = combine_scrubbers(temp_path_scrubber, date_scrubber)
        
        verify(result, options=Options().with_scrubber(multi_scrubber))

    def test_tool_cat_integration(self, capsys, tmp_path):
        temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
        result = self.run_chat_test(capsys, input_stub=self.enter_input, message="Test message", answer=f"/cat {temp_file}")
        
        temp_path_scrubber = create_regex_scrubber(str(temp_file).replace('\\', '\\\\'), '/tmp/test_path/integration_test.txt')
        verify(result, options=Options().with_scrubber(temp_path_scrubber))

    def test_multiple_tool_calls_integration(self, capsys, tmp_path):
        temp_file = create_temp_file(tmp_path, "multi_test.txt", "Multi-tool test")
        ls_result = self.run_chat_test(capsys, input_stub=self.enter_input, message="Test message", answer=f"/ls {tmp_path}")
        cat_result = self.run_chat_test(capsys, input_stub=self.enter_input, message="Test message", answer=f"/cat {temp_file}")
        
        combined_result = f"=== LS RESULT ===\n{ls_result}\n\n=== CAT RESULT ===\n{cat_result}"
        temp_path_scrubber = create_regex_scrubber(str(tmp_path).replace('\\', '\\\\'), '/tmp/test_path')
        date_scrubber = create_regex_scrubber(r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', '[DATE]')
        multi_scrubber = combine_scrubbers(temp_path_scrubber, date_scrubber)
        
        verify(combined_result, options=Options().with_scrubber(multi_scrubber))

    def test_chat_with_regular_response(self, capsys):
        result = self.run_chat_test(capsys, input_stub=self.enter_input, message="Hello", answer="Hello! How can I help you?")
        verify(result)
