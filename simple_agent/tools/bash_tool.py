import os
import subprocess
import sys

from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult, ToolResultStatus
from .base_tool import BaseTool


class BashTool(BaseTool):
    name = "bash"
    description = "Execute bash commands. Tip: Avoid grep, but use ripgrep (the rg command) for search. To run a command in the background, end it with an ampersand (&)."
    arguments = ToolArguments(
        header=[
            ToolArgument(
                name="command",
                type="string",
                required=True,
                description="The bash command to execute",
            )
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
            "reasoning": "To start a long-running process in the background:",
            "command": "sleep 10 &",
            "result": "✅ Process started in background with PID: 12345",
        },
    ]

    async def execute(self, raw_call):
        args = raw_call.arguments
        if not args:
            return SingleToolResult(
                "STDERR: bash: missing command", status=ToolResultStatus.FAILURE
            )

        # Check if command should be run in the background
        if args.strip().endswith("&"):
            try:
                # Use Popen for non-blocking execution.
                # preexec_fn=os.setsid is used to run the command in a new session,
                # detaching it from the current process. This is Unix-specific.
                popen_kwargs = {
                    "stdout": subprocess.DEVNULL,
                    "stderr": subprocess.DEVNULL,
                    "stdin": subprocess.DEVNULL,
                }
                if hasattr(os, "setsid"):
                    popen_kwargs["preexec_fn"] = os.setsid
                elif sys.platform == "win32":
                    # On Windows, use CREATE_NEW_PROCESS_GROUP or DETACHED_PROCESS
                    # to achieve similar detachment.
                    popen_kwargs["creationflags"] = (
                        subprocess.CREATE_NEW_PROCESS_GROUP
                        | subprocess.DETACHED_PROCESS
                    )

                process = subprocess.Popen(["bash", "-c", args], **popen_kwargs)
                return SingleToolResult(
                    f"✅ Process started in background with PID: {process.pid}",
                    status=ToolResultStatus.SUCCESS,
                )
            except Exception as e:
                return SingleToolResult(
                    f"❌ Failed to start process in background: {e}",
                    status=ToolResultStatus.FAILURE,
                )

        # Original synchronous execution
        _ = subprocess
        result = await self.run_command_async("bash", ["-c", args])

        output = result["output"]
        elapsed_time = result.get("elapsed_time", 0)
        exit_code = 0 if result["success"] else 1
        status_icon = "✅" if result["success"] else "❌"

        if output:
            formatted_output = f"{status_icon} Exit code {exit_code} ({elapsed_time:.3f}s elapsed)\n\n{output}"
        else:
            formatted_output = (
                f"{status_icon} Exit code {exit_code} ({elapsed_time:.3f}s elapsed)"
            )

        status = (
            ToolResultStatus.SUCCESS if result["success"] else ToolResultStatus.FAILURE
        )
        return SingleToolResult(formatted_output, status=status)
