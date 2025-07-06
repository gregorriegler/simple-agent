from modernizer.tools.tool_library import ToolLibrary
from .test_helpers import (
    create_temp_directory_structure,
    verifyTool
)

library = ToolLibrary()

def test_ls_tool_basic_directory(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    
    verifyTool(library, f"/ls {directory_path}")

def test_ls_tool_nonexistent_directory():
    verifyTool(library, "/ls /nonexistent/path")