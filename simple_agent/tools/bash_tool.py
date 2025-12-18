import subprocess
from ..application.tool_library import ContinueResult, ToolArgument, ToolArguments
from .base_tool import BaseTool


class BashTool(BaseTool):
    name = 'bash'
    description = "Execute bash commands"
    arguments = ToolArguments(header=[
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

        output = result['output']
        elapsed_time = result.get('elapsed_time', 0)
        exit_code = 0 if result['success'] else 1
        status_icon = "✅" if result['success'] else "❌"

        if output:
            formatted_output = f"{status_icon} Exit code {exit_code} ({elapsed_time:.3f}s elapsed)\n\n{output}"
        else:
            formatted_output = f"{status_icon} Exit code {exit_code} ({elapsed_time:.3f}s elapsed)"

        return ContinueResult(formatted_output, success=result['success'])
