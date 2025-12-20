import os
import shutil
import subprocess
import sys

import pytest

from tests.test_helpers import create_all_tools_for_test, verify_tool

library = create_all_tools_for_test()
pytestmark = pytest.mark.asyncio
bash_available = True


def _bash_available() -> bool:
    bash_path = shutil.which("bash")
    if not bash_path:
        return False
    if sys.platform != "win32":
        return True
    normalized = os.path.normcase(os.path.normpath(bash_path))
    if normalized.endswith(os.path.normcase(r"\system32\bash.exe")):
        result = subprocess.run(
            ["wsl.exe", "-l", "-q"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    return True


bash_available = _bash_available()
if not bash_available:
    pytest.skip("bash is not available on this platform", allow_module_level=True)


async def test_bash_tool_success_stdout():
    await verify_tool(library, "🛠️[bash printf 'hello world' /]")


async def test_bash_tool_stderr_output():
    await verify_tool(library, "🛠️[bash printf 'warning' 1>&2 /]")


async def test_bash_tool_nonzero_exit():
    await verify_tool(library, "🛠️[bash exit 2 /]")


async def test_bash_tool_fail_with_stdout_and_stderr():
    await verify_tool(library, "🛠️[bash echo 'standard output' && echo 'error output' >&2 && exit 1 /]")
