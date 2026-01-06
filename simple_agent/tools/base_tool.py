import asyncio
import subprocess
import time
from typing import Dict

from simple_agent.application.tool_library import Tool, ToolArguments
from simple_agent.application.tool_results import ToolResult
from simple_agent.application.tool_syntax import RawToolCall


class BaseTool(Tool):
    name = ""
    description = ""
    arguments: ToolArguments = ToolArguments(header=[], body=None)
    examples = []

    async def execute(self, raw_call: RawToolCall) -> ToolResult:
        raise NotImplementedError("Subclasses must implement execute()")

    @staticmethod
    def run_command(command, args=None, cwd=None):
        try:
            command_line = [command]
            if args:
                if isinstance(args, str):
                    args = [args]
                command_line += args

            start_time = time.time()
            result = subprocess.run(
                command_line,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=cwd,
            )
            elapsed_time = time.time() - start_time

            output = result.stdout.rstrip("\n")
            if result.stderr:
                if output:
                    output += "\n"
                output += f"STDERR: {result.stderr}"
            return {
                "output": output,
                "success": result.returncode == 0,
                "elapsed_time": elapsed_time,
            }
        except subprocess.TimeoutExpired:
            return {
                "output": "Command timed out (30s limit)",
                "success": False,
                "elapsed_time": 30.0,
            }
        except Exception as e:
            return {"output": f"Error: {str(e)}", "success": False, "elapsed_time": 0.0}

    @staticmethod
    async def run_command_async(command, args=None, cwd=None):
        return await asyncio.to_thread(BaseTool.run_command, command, args, cwd)

    def get_template_variables(self) -> Dict[str, str]:
        """Return variables to substitute in documentation templates.

        Override this method to provide runtime values for template placeholders
        like {{VARIABLE_NAME}} in tool descriptions or arguments.
        """
        return {}
