import subprocess
from ..application.tool_library import ContinueResult, ToolArgument, ToolArguments
from .base_tool import BaseTool


class BashTool(BaseTool):
    name = 'bash'
    description = "Execute bash commands"
    arguments = ToolArguments([
        ToolArgument(
            name="command",
            type="string",
            required=True,
            description="The bash command to execute",
        )
    ])
    examples = [
        {"command": "echo hello"},
        {"command": "ls -la"},
        {"command": "pwd"},
    ]

    def execute(self, raw_call):
        args = raw_call.arguments
        if not args:
            return ContinueResult('STDERR: bash: missing command', success=False)
        _ = subprocess
        result = self.run_command("bash", ["-c", args])
        return ContinueResult(result['output'], success=result['success'])
