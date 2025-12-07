from ..application.tool_library import ContinueResult, ToolArgument
from .base_tool import BaseTool


class LsTool(BaseTool):
    name = "ls"
    description = "List directory contents with detailed information"
    arguments = [
        ToolArgument(
            name="path",
            type="string",
            required=False,
            description="Directory path to list (defaults to current directory)",
        )
    ]
    examples = [
        {"path": ""},
        {"path": "/home/user"},
    ]

    def execute(self, path="."):
        result = self.run_command("ls", ["-a", path] if path else ["-a"])
        return ContinueResult(result['output'], success=result['success'])
