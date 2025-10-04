from simple_agent.tools.tool_library import ToolLibrary
from .test_helpers import (
    create_temp_directory_structure,
    verify_tool
)

claude_stub = lambda system_prompt, messages: ""
library = ToolLibrary()


def test_ls_tool_basic_directory(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)

    verify_tool(library, f"🛠️ ls {directory_path}")

def test_ls_tool_nonexistent_directory():
    verify_tool(library, "🛠️ ls /nonexistent/path")
