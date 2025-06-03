import os
import sys
from approvaltests import verify
from approvaltests import Options

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modernizer.tools.tool_library import ToolLibrary
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure,
    create_path_scrubber,
    create_date_scrubber,
    create_multi_scrubber
)

framework = ToolLibrary()


def test_ls_tool_basic_directory(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    
    command, result = framework.parse_and_execute(f"/ls {directory_path}")
    
    multi_scrubber = create_multi_scrubber()
    
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(multi_scrubber))

def test_ls_tool_nonexistent_directory():
    command, result = framework.parse_and_execute("/ls /nonexistent/path")
    
    date_scrubber = create_date_scrubber()
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(date_scrubber))

def test_cat_tool_single_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "Hello world\nSecond line\nThird line")
    
    command, result = framework.parse_and_execute(f"/cat {temp_file}")
    
    path_scrubber = create_path_scrubber('/tmp/test_path/test.txt')
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(path_scrubber))

def test_cat_tool_nonexistent_file():
    command, result = framework.parse_and_execute("/cat /nonexistent/file.txt")
    
    verify(f"Command: {command}\nResult: {result}")

def test_cat_tool_empty_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "empty.txt", "")
    
    command, result = framework.parse_and_execute(f"/cat {temp_file}")
    
    path_scrubber = create_path_scrubber('/tmp/test_path/empty.txt')
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(path_scrubber))

def test_unknown_command():
    command, result = framework.parse_and_execute("/unknown-command arg1 arg2")
    
    verify(f"Command: {command}\nResult: {result}")

def test_no_command_in_text():
    command, result = framework.parse_and_execute("This is just regular text without commands")
    
    verify(f"Command: {command}\nResult: {result}")

def test_tool_with_special_characters(tmp_path):
    special_file = create_temp_file(tmp_path, "special-file_name.txt", "Content with special chars: !@#$%^&*()")
    command, result = framework.parse_and_execute(f"/cat {special_file}")
    
    path_scrubber = create_path_scrubber('/tmp/test_path/special-file_name.txt')
    verify(f"Command: {command}\nResult: {result}", options=Options().with_scrubber(path_scrubber))
