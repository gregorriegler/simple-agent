from tools.tool_library import ToolLibrary
from .test_helpers import verifyTool

library = ToolLibrary()

def test_unknown_command():
    verifyTool(library, "/unknown-command arg1 arg2")

def test_no_command_in_text():
    verifyTool(library, "This is just regular text without commands")

