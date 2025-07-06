from modernizer.tools.tool_library import ToolLibrary
from .test_helpers import (
    create_temp_file,
    verifyTool
)

library = ToolLibrary()

def test_cat_tool_single_line_from_beginning(tmp_path):
    """Test extracting a single line from the beginning of a file using range 1-1"""
    temp_file = create_temp_file(tmp_path, "single_line_test.txt", "first line content\nsecond line\nthird line")
    
    verifyTool(library, f"/cat {temp_file} 1-1")