from modernizer.tools.tool_library import ToolLibrary
from .test_helpers import (
    create_temp_file,
    verifyTool
)

library = ToolLibrary()

def test_cat_tool_multiple_lines_from_beginning(tmp_path):
    """Test extracting multiple lines from the beginning of a file using range 1-3"""
    temp_file = create_temp_file(tmp_path, "multiple_lines_test.txt", "first line content\nsecond line\nthird line\nfourth line")
    
    verifyTool(library, f"/cat {temp_file} 1-3")