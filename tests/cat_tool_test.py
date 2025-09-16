from tools.tool_library import ToolLibrary
from .test_helpers import (
    create_temp_file,
    verify_tool
)

library = ToolLibrary()

def test_cat_tool_single_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "Hello world\nSecond line\nThird line")

    verify_tool(library, f"🛠️ cat {temp_file}")

def test_cat_tool_nonexistent_file():
    verify_tool(library, "🛠️ cat /nonexistent/file.txt")

def test_cat_tool_empty_file(tmp_path):
    temp_file = create_temp_file(tmp_path, "empty.txt", "")

    verify_tool(library, f"🛠️ cat {temp_file}")

def test_cat_tool_empty_file_with_range(tmp_path):
    temp_file = create_temp_file(tmp_path, "empty.txt", "")

    verify_tool(library, f"🛠️ cat {temp_file} 1-5")

def test_cat_tool_with_special_characters(tmp_path):
    special_file = create_temp_file(tmp_path, "special-file_name.txt", "Content with special chars: !@#$%^&*()")

    verify_tool(library, f"🛠️ cat {special_file}")

def test_cat_tool_single_line_from_beginning(tmp_path):
    temp_file = create_temp_file(tmp_path, "single_line_test.txt", "first line content\nsecond line\nthird line")

    verify_tool(library, f"🛠️ cat {temp_file} 1-1")

def test_cat_tool_multiple_lines_from_beginning(tmp_path):
    temp_file = create_temp_file(tmp_path, "multiple_lines_test.txt", "first line content\nsecond line\nthird line\nfourth line")

    verify_tool(library, f"🛠️ cat {temp_file} 1-3")

def test_cat_tool_specific_line_range(tmp_path):
    content = "\n".join([f"Line {i} content" for i in range(1, 16)])
    temp_file = create_temp_file(tmp_path, "range_test.txt", content)

    verify_tool(library, f"🛠️ cat {temp_file} 5-10")

def test_cat_tool_invalid_range_format(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")

    verify_tool(library, f"🛠️ cat {temp_file} abc-def")

def test_cat_tool_reversed_range(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")

    verify_tool(library, f"🛠️ cat {temp_file} 10-5")

def test_cat_tool_range_beyond_file_length(tmp_path):
    temp_file = create_temp_file(tmp_path, "test.txt", "line 1\nline 2\nline 3")

    verify_tool(library, f"🛠️ cat {temp_file} 100-200")

def test_cat_tool_file_with_spaces(tmp_path):
    temp_file = create_temp_file(tmp_path, "file with spaces.txt", "line 1\nline 2")

    verify_tool(library, f"🛠️ cat '{temp_file}'")

def test_cat_tool_range_with_spaces(tmp_path):
    temp_file = create_temp_file(tmp_path, "range spaces.txt", "first\nsecond\nthird")

    verify_tool(library, f"🛠️ cat '{temp_file}' '1 - 2'")

def test_cat_tool_nonexistent_file_with_range():
    verify_tool(library, "🛠️ cat /nonexistent/file.txt 1-5")
