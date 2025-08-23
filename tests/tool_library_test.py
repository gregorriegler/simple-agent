from tools.tool_library import ToolLibrary
from .test_helpers import verify_tool

library = ToolLibrary()

def test_unknown_command():
    verify_tool(library, "/unknown-command arg1 arg2")

def test_no_command_in_text():
    verify_tool(library, "This is just regular text without commands")

