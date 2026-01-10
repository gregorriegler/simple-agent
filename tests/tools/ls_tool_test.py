import pytest

from tests.test_helpers import (
    create_temp_directory_structure,
    verify_tool,
)


def claude_stub(messages):
    return ""


pytestmark = pytest.mark.asyncio


async def test_ls_tool_basic_directory(tmp_path, tool_library):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)

    await verify_tool(tool_library, f"🛠️[ls {directory_path} /]")


async def test_ls_tool_nonexistent_directory(tool_library):
    await verify_tool(tool_library, "🛠️[ls /nonexistent/path /]")
