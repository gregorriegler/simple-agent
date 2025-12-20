import pytest

from tests.test_helpers import create_all_tools_for_test, verify_tool

library = create_all_tools_for_test()
pytestmark = pytest.mark.asyncio


async def test_bash_tool_success_stdout():
    await verify_tool(library, "🛠️[bash printf 'hello world' /]")


async def test_bash_tool_stderr_output():
    await verify_tool(library, "🛠️[bash printf 'warning' 1>&2 /]")


async def test_bash_tool_nonzero_exit():
    await verify_tool(library, "🛠️[bash exit 2 /]")


async def test_bash_tool_fail_with_stdout_and_stderr():
    await verify_tool(library, "🛠️[bash echo 'standard output' && echo 'error output' >&2 && exit 1 /]")
