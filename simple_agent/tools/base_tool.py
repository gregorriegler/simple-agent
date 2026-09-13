import asyncio
import time

from simple_agent.application.tool_library import Tool, ToolArguments, ToolCall
from simple_agent.application.tool_results import ToolResult

TIMEOUT = 60


class BaseTool(Tool):
    name = ""
    description = ""
    arguments: ToolArguments = ToolArguments(header=[], body=None)
    examples = []

    async def execute(self, call: ToolCall) -> ToolResult:
        raise NotImplementedError("Subclasses must implement execute()")

    @staticmethod
    async def run_command_async(command, args=None, cwd=None):
        command_line = [command]
        if args:
            if isinstance(args, str):
                args = [args]
            command_line += args

        start_time = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                *command_line,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
        except Exception as e:
            return {"output": f"Error: {str(e)}", "success": False, "elapsed_time": 0.0}

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), TIMEOUT)
        except TimeoutError:
            process.kill()
            await process.wait()
            return {
                "output": "Command timed out (" + str(TIMEOUT) + "s limit)",
                "success": False,
                "elapsed_time": TIMEOUT,
            }
        except asyncio.CancelledError:
            process.kill()
            await process.wait()
            raise

        output = stdout.decode("utf-8", errors="replace").rstrip("\n")
        error_output = stderr.decode("utf-8", errors="replace")
        if error_output:
            if output:
                output += "\n"
            output += f"STDERR: {error_output}"
        return {
            "output": output,
            "success": process.returncode == 0,
            "elapsed_time": time.time() - start_time,
        }
