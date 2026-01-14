import pytest

from tests.test_helpers import verify_tool

pytestmark = pytest.mark.asyncio


async def test_bash_tool_background_execution(tool_library):
    # This should not fail even on Windows/MSYS
    await verify_tool(tool_library, "🛠️[bash sleep 1 & /]")
