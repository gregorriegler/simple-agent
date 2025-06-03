import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modernizer.tools.tool_library import ToolLibrary
from .test_helpers import (
    create_temp_file,
    create_temp_directory_structure,
    verifyTool
)

framework = ToolLibrary()


def test_ls_tool_basic_directory(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    
    verifyTool(framework, f"/ls {directory_path}")

def test_ls_tool_nonexistent_directory():
    verifyTool(framework, "/ls /nonexistent/path")

def test_cat_tool_single_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "Hello world\nSecond line\nThird line")
    
    verifyTool(framework, f"/cat {temp_file}")

def test_cat_tool_nonexistent_file():
    verifyTool(framework, "/cat /nonexistent/file.txt")

def test_cat_tool_empty_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "empty.txt", "")
    
    verifyTool(framework, f"/cat {temp_file}")

def test_unknown_command():
    verifyTool(framework, "/unknown-command arg1 arg2")

def test_no_command_in_text():
    verifyTool(framework, "This is just regular text without commands")

def test_tool_with_special_characters(tmp_path):
    special_file = create_temp_file(tmp_path, "special-file_name.txt", "Content with special chars: !@#$%^&*()")
    
    verifyTool(framework, f"/cat {special_file}")
