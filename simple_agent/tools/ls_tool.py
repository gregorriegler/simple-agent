from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult, ToolResultStatus
from .base_tool import BaseTool


class LsTool(BaseTool):
    name = "ls"
    description = "List directory contents with detailed information"
    arguments = ToolArguments(header=[
        ToolArgument(
            name="path",
            type="string",
            required=False,
            description="Directory path to list (defaults to current directory)",
        )
    ])
    examples = [
        {
            "reasoning": "I'll list files in the current directory.",
            "path": "",
            "result": "total 48\ndrwxr-xr-x  5 user  staff   160 Dec 19 10:30 .\ndrwxr-xr-x 10 user  staff   320 Dec 19 10:25 ..\n-rw-r--r--  1 user  staff  1234 Dec 19 10:30 file.txt"
        },
        {"path": "/home/user"},
    ]

    async def execute(self, raw_call):
        path = raw_call.arguments if raw_call.arguments else "."
        result = await self.run_command_async("ls", ["-a", path] if path else ["-a"])
        status = ToolResultStatus.SUCCESS if result['success'] else ToolResultStatus.FAILURE
        return SingleToolResult(result['output'], status=status)
