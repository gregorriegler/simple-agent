from tools.tool_library import ToolLibrary
from .test_helpers import (
    verify_tool
)

library = ToolLibrary()

def test_simple_subtask():
    verify_tool(library, f"/subagent say hello")
