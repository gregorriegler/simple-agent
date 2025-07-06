from modernizer.tools.tool_library import ToolLibrary
from .test_helpers import (
    create_temp_file,
    verifyTool
)

library = ToolLibrary()

def test_cat_tool_single_file(tmp_path):
    """Test displaying a file with line numbers"""
    temp_file = create_temp_file(tmp_path, "test.txt", "Hello world\nSecond line\nThird line")
    
    verifyTool(library, f"/cat {temp_file}")

def test_cat_tool_nonexistent_file():
    """Test cat tool with nonexistent file"""
    verifyTool(library, "/cat /nonexistent/file.txt")

def test_cat_tool_empty_file(tmp_path):
    """Test cat tool with empty file"""
    temp_file = create_temp_file(tmp_path, "empty.txt", "")
    
    verifyTool(library, f"/cat {temp_file}")

def test_cat_tool_empty_file_with_range(tmp_path):
    """Test cat tool with empty file and range"""
    temp_file = create_temp_file(tmp_path, "empty.txt", "")
    
    verifyTool(library, f"/cat {temp_file} 1-5")

def test_cat_tool_with_special_characters(tmp_path):
    """Test cat tool with file containing special characters"""
    special_file = create_temp_file(tmp_path, "special-file_name.txt", "Content with special chars: !@#$%^&*()")
    
    verifyTool(library, f"/cat {special_file}")

def test_cat_tool_single_line_from_beginning(tmp_path):
    """Test extracting a single line from the beginning of a file using range 1-1"""
    temp_file = create_temp_file(tmp_path, "single_line_test.txt", "first line content\nsecond line\nthird line")
    
    verifyTool(library, f"/cat {temp_file} 1-1")

def test_cat_tool_multiple_lines_from_beginning(tmp_path):
    """Test extracting multiple lines from the beginning of a file using range 1-3"""
    temp_file = create_temp_file(tmp_path, "multiple_lines_test.txt", "first line content\nsecond line\nthird line\nfourth line")
    
    verifyTool(library, f"/cat {temp_file} 1-3")

def test_cat_tool_specific_line_range(tmp_path):
    """Test displaying specific line range (5-10) with original line numbers preserved"""
    # Create a file with 15 lines to test range 5-10
    content = "\n".join([f"Line {i} content" for i in range(1, 16)])
    temp_file = create_temp_file(tmp_path, "range_test.txt", content)
    
    verifyTool(library, f"/cat {temp_file} 5-10")

def test_cat_tool_invalid_range_format(tmp_path):
    """Test cat tool with invalid range format (abc-def) expects clear error message"""
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")
    
    verifyTool(library, f"/cat {temp_file} abc-def")

def test_cat_tool_reversed_range(tmp_path):
    """Test cat tool with reversed range (10-5) where start line is greater than end line"""
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")
    
    verifyTool(library, f"/cat {temp_file} 10-5")

def test_cat_tool_range_beyond_file_length(tmp_path):
    """Test cat tool with range beyond file length (100-200) on a file with only 3 lines"""
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")
    
    verifyTool(library, f"/cat {temp_file} 100-200")

def test_cat_tool_nonexistent_file_with_range():
    """Test cat tool with nonexistent file and range expects same file not found error"""
    verifyTool(library, "/cat /nonexistent/file.txt 1-5")