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

def test_ls_lists_directory_contents(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    subdir = tmp_path / "subdir"
    file1.write_text("hello")
    file2.write_text("world")
    subdir.mkdir()

    framework = ToolLibrary()
    
    _, tool_result = framework.parse_and_execute("/ls " + str(tmp_path))
    
    assert "file1.txt" in tool_result
    assert "file2.txt" in tool_result
    assert "subdir" in tool_result


def test_cat_shows_contents(tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.write_text("hello")
    
    framework = ToolLibrary()

    _, tool_result = framework.parse_and_execute("/cat " + str(file1))

    assert "1\thello" == tool_result
    
def xtest_test_runs_test():
    framework = ToolLibrary()
    
    _, tool_result = framework.parse_and_execute("/test ../refactoring-tools")
    
    assert "All tests passed" in tool_result
    
def xtest_extract_method():
    framework = ToolLibrary()
    
    _, tool_result = framework.parse_and_execute("/extract-method \"C:/Users/riegl/code/Parrot-Refactoring-Kata/CSharp/Parrot/Parrot.csproj\" Parrot.cs 23:0-33:14 ComputeSpeed")
    
    print(tool_result)
    assert "x" is tool_result

def test_ls_tool_basic_directory(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    
    framework = ToolLibrary()
    command, result = framework.parse_and_execute(f"/ls {directory_path}")
    
    temp_path_scrubber = create_regex_scrubber(str(directory_path).replace('\\', '\\\\'), '/tmp/test_path')
    date_scrubber = create_regex_scrubber(r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', '[DATE]')
    multi_scrubber = combine_scrubbers(temp_path_scrubber, date_scrubber)
    
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(multi_scrubber))

def test_ls_tool_nonexistent_directory():
    framework = ToolLibrary()
    command, result = framework.parse_and_execute("/ls /nonexistent/path")
    
    date_scrubber = create_regex_scrubber(r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', '[DATE]')
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(date_scrubber))

def test_cat_tool_single_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "Hello world\nSecond line\nThird line")
    
    framework = ToolLibrary()
    command, result = framework.parse_and_execute(f"/cat {temp_file}")
    
    temp_path_scrubber = create_regex_scrubber(str(temp_file).replace('\\', '\\\\'), '/tmp/test_path/test.txt')
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(temp_path_scrubber))

def test_cat_tool_nonexistent_file():
    framework = ToolLibrary()
    command, result = framework.parse_and_execute("/cat /nonexistent/file.txt")
    
    verify(f"Command: {command}\nResult: {result}")

def test_cat_tool_empty_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "empty.txt", "")
    
    framework = ToolLibrary()
    command, result = framework.parse_and_execute(f"/cat {temp_file}")
    
    temp_path_scrubber = create_regex_scrubber(str(temp_file).replace('\\', '\\\\'), '/tmp/test_path/empty.txt')
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(temp_path_scrubber))

def test_unknown_command():
    framework = ToolLibrary()
    command, result = framework.parse_and_execute("/unknown-command arg1 arg2")
    
    verify(f"Command: {command}\nResult: {result}")

def test_no_command_in_text():
    framework = ToolLibrary()
    command, result = framework.parse_and_execute("This is just regular text without commands")
    
    verify(f"Command: {command}\nResult: {result}")

def test_tool_with_special_characters(tmp_path):
    special_file = create_temp_file(tmp_path, "special-file_name.txt", "Content with special chars: !@#$%^&*()")
    framework = ToolLibrary()
    command, result = framework.parse_and_execute(f"/cat {special_file}")
    
    temp_path_scrubber = create_regex_scrubber(str(special_file).replace('\\', '\\\\'), '/tmp/test_path/special-file_name.txt')
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(temp_path_scrubber))
