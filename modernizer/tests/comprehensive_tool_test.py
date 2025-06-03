import builtins
import os
import sys
import pytest
from approvaltests import verify
from approvaltests.reporters.report_with_beyond_compare import ReportWithWinMerge
from approvaltests import set_default_reporter
from approvaltests.scrubbers import create_regex_scrubber, combine_scrubbers
from approvaltests import Options

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modernizer.tools.tool_library import ToolLibrary
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

class TestToolLibrary:
    def test_ls_tool_basic_directory(self, tmp_path):
        directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
        
        framework = ToolLibrary()
        command, result = framework.parse_and_execute(f"/ls {directory_path}")
        
        temp_path_scrubber = create_regex_scrubber(str(directory_path).replace('\\', '\\\\'), '/tmp/test_path')
        date_scrubber = create_regex_scrubber(r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', '[DATE]')
        multi_scrubber = combine_scrubbers(temp_path_scrubber, date_scrubber)
        
        verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(multi_scrubber))

    def test_ls_tool_nonexistent_directory(self):
        framework = ToolLibrary()
        command, result = framework.parse_and_execute("/ls /nonexistent/path")
        
        date_scrubber = create_regex_scrubber(r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', '[DATE]')
        verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(date_scrubber))

    def test_cat_tool_single_file(self, tmp_path):
        temp_file = create_temp_file(tmp_path, "test.txt", "Hello world\nSecond line\nThird line")
        
        framework = ToolLibrary()
        command, result = framework.parse_and_execute(f"/cat {temp_file}")
        
        temp_path_scrubber = create_regex_scrubber(str(temp_file).replace('\\', '\\\\'), '/tmp/test_path/test.txt')
        verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(temp_path_scrubber))

    def test_cat_tool_nonexistent_file(self):
        framework = ToolLibrary()
        command, result = framework.parse_and_execute("/cat /nonexistent/file.txt")
        
        verify(f"Command: {command}\nResult: {result}")

    def test_cat_tool_empty_file(self, tmp_path):
        temp_file = create_temp_file(tmp_path, "empty.txt", "")
        
        framework = ToolLibrary()
        command, result = framework.parse_and_execute(f"/cat {temp_file}")
        
        temp_path_scrubber = create_regex_scrubber(str(temp_file).replace('\\', '\\\\'), '/tmp/test_path/empty.txt')
        verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(temp_path_scrubber))

    def test_unknown_command(self):
        framework = ToolLibrary()
        command, result = framework.parse_and_execute("/unknown-command arg1 arg2")
        
        verify(f"Command: {command}\nResult: {result}")

    def test_no_command_in_text(self):
        framework = ToolLibrary()
        command, result = framework.parse_and_execute("This is just regular text without commands")
        
        verify(f"Command: {command}\nResult: {result}")

    def test_tool_library_initialization(self):
        framework = ToolLibrary()
        expected_tools = ['ls', 'cat', 'test', 'extract-method', 'inline-method', 'revert']
        actual_tools = list(framework.tool_dict.keys())
        result = f"Expected tools: {sorted(expected_tools)}\nActual tools: {sorted(actual_tools)}\nAll tools present: {set(expected_tools).issubset(set(actual_tools))}"
        verify(result)

    def test_tool_with_special_characters(self, tmp_path):
        special_file = create_temp_file(tmp_path, "special-file_name.txt", "Content with special chars: !@#$%^&*()")
        framework = ToolLibrary()
        command, result = framework.parse_and_execute(f"/cat {special_file}")
        
        temp_path_scrubber = create_regex_scrubber(str(special_file).replace('\\', '\\\\'), '/tmp/test_path/special-file_name.txt')
        verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(temp_path_scrubber))


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