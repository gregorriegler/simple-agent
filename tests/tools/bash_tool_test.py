import asyncio
import os
import shutil
import subprocess
import sys

import pytest

from tests.test_helpers import execute_call, verify_tool
from tests.tool_calls import bash

pytestmark = pytest.mark.asyncio
bash_available = True


def _bash_available() -> bool:
    bash_path = shutil.which("bash")
    if not bash_path:
        return False
    if sys.platform == "win32":
        normalized = os.path.normcase(os.path.normpath(bash_path))
        if normalized.endswith(os.path.normcase(r"\system32\bash.exe")):
            result = subprocess.run(
                ["wsl.exe", "-l", "-q"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and not result.stdout.strip():
                return False
    try:
        result = subprocess.run(
            ["bash", "-c", "printf 'ok'"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    if result.returncode != 0:
        return False
    return result.stdout == "ok"


bash_available = _bash_available()
if not bash_available:
    pytest.skip("bash is not available on this platform", allow_module_level=True)


async def test_a_cancelled_bash_call_kills_its_process(tool_library, tmp_path):
    pid_file = tmp_path / "pid"
    running = asyncio.create_task(
        execute_call(tool_library, bash(f"echo $$ > {pid_file}; sleep 30"))
    )
    while not pid_file.exists():
        await asyncio.sleep(0.01)

    running.cancel()
    with pytest.raises(asyncio.CancelledError):
        await running

    await asyncio.sleep(0.1)
    assert not _is_alive(int(pid_file.read_text()))


def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


async def test_bash_tool_success_stdout(tool_library):
    await verify_tool(tool_library, bash("printf 'hello world'"))


async def test_bash_tool_stderr_output(tool_library):
    await verify_tool(tool_library, bash("printf 'warning' 1>&2"))


async def test_bash_tool_nonzero_exit(tool_library):
    await verify_tool(tool_library, bash("exit 2"))


async def test_bash_tool_fail_with_stdout_and_stderr(tool_library):
    await verify_tool(
        tool_library,
        bash("echo 'standard output' && echo 'error output' >&2 && exit 1"),
    )
