import pytest

from tests.test_helpers import (
    create_all_tools_for_test,
    create_temp_directory_structure,
    verify_tool,
)

def claude_stub(messages):
    return ""

library = create_all_tools_for_test()
pytestmark = pytest.mark.asyncio


async def test_ls_tool_basic_directory(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)

    await verify_tool(library, f"🛠️[ls {directory_path} /]")


async def test_ls_tool_nonexistent_directory():
    await verify_tool(library, "🛠️[ls /nonexistent/path /]")
