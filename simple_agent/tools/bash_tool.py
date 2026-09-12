import asyncio
import os
import shutil
import sys
import time
from collections.abc import Callable
from pathlib import PureWindowsPath

from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult, ToolResultStatus
from .base_tool import BaseTool


def bash_executable() -> str:
    found = shutil.which("bash")
    if sys.platform != "win32" or found is None:
        return found or "bash"
    if not found.lower().replace("/", "\\").endswith("\\system32\\bash.exe"):
        return found
    return _git_bash() or found


def _git_bash() -> str | None:
    git = shutil.which("git")
    if git is None:
        return None
    root = PureWindowsPath(git).parent.parent
    for candidate in (root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"):
        if os.path.exists(str(candidate)):
            return str(candidate)
    return None


class BashTool(BaseTool):
    name = "bash"
    description = "Execute bash commands. Tip: Avoid grep, but use ripgrep (the rg command) for search."
    arguments = ToolArguments(
        header=[
            ToolArgument(
                name="command",
                type="string",
                required=True,
                description="The bash command to execute",
            ),
            ToolArgument(
                name="--background",
                type="bool",
                required=False,
                description="Run the command in the background: return immediately, and receive its output as a message once it finishes.",
            ),
        ]
    )
    examples = [
        {
            "reasoning": "The user asks you to change something in the main function and you need to find it:",
            "command": r"rg 'main\(' -g '*.py'",
            "result": "✅ Exit code 0 (0.068s elapsed)\n\nfoo.py\n82:def main() -> None:\n97:    main()",
        },
        {
            "reasoning": "Let's say you need to echo a message. Then you should send:",
            "command": "echo hello world",
            "result": "✅ Exit code 0 (0.068s elapsed)\n\nhello world",
        },
        {
            "reasoning": "Let me list the files in detail.",
            "command": "ls -la",
        },
        {
            "reasoning": "To start a long-running process and carry on while it runs:",
            "command": "bash test.sh",
            "--background": True,
            "result": "✅ Process started in background with PID: 12345",
        },
    ]

    def __init__(self, report: Callable[[str], None] | None = None):
        super().__init__()
        self._report = report or (lambda message: None)
        self._background: set[asyncio.Task] = set()

    async def execute(self, call):
        args = str(call.named_arguments.get("command", ""))
        if not args:
            return SingleToolResult(
                "STDERR: bash: missing command", status=ToolResultStatus.FAILURE
            )
        if call.named_arguments.get("--background", False):
            return await self._start_in_background(args)

        result = await self.run_command_async(bash_executable(), ["-c", args])
        exit_code = 0 if result["success"] else 1
        return SingleToolResult(
            _format(result["output"], exit_code, result.get("elapsed_time", 0)),
            status=ToolResultStatus.SUCCESS
            if result["success"]
            else ToolResultStatus.FAILURE,
        )

    async def _start_in_background(self, command: str) -> SingleToolResult:
        try:
            process = await asyncio.create_subprocess_exec(
                bash_executable(),
                "-c",
                command,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except Exception as e:
            return SingleToolResult(
                f"❌ Failed to start process in background: {e}",
                status=ToolResultStatus.FAILURE,
            )
        task = asyncio.create_task(self._report_when_done(command, process))
        self._background.add(task)
        task.add_done_callback(self._background.discard)
        return SingleToolResult(
            f"✅ Process started in background with PID: {process.pid}"
        )

    async def _report_when_done(self, command: str, process) -> None:
        started = time.time()
        stdout, stderr = await process.communicate()
        elapsed = time.time() - started
        output = stdout.decode("utf-8", errors="replace").rstrip("\n")
        if stderr:
            if output:
                output += "\n"
            output += f"STDERR: {stderr.decode('utf-8', errors='replace')}"
        self._report(
            f"Background command `{command}` finished:\n"
            f"{_format(output, process.returncode, elapsed)}"
        )


def _format(output: str, exit_code: int, elapsed: float) -> str:
    icon = "✅" if exit_code == 0 else "❌"
    header = f"{icon} Exit code {exit_code} ({elapsed:.3f}s elapsed)"
    return f"{header}\n\n{output}" if output else header
