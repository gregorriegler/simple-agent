import subprocess
from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult, ToolResultStatus
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
        {
            "reasoning": "Let's say you need to echo a message. Then you should send:",
            "command": "echo hello world",
            "result": "✅ Exit code 0 (0.068s elapsed)\n\nhello world"
        },
        {
            "reasoning": "Let me list the files in detail.",
            "command": "ls -la",
        },
    ]

    async def execute(self, raw_call):
        args = raw_call.arguments
        if not args:
            return SingleToolResult('STDERR: bash: missing command', status=ToolResultStatus.FAILURE)
        _ = subprocess
        result = await self.run_command_async("bash", ["-c", args])

        output = result['output']
        elapsed_time = result.get('elapsed_time', 0)
        exit_code = 0 if result['success'] else 1
        status_icon = "✅" if result['success'] else "❌"

        if output:
            formatted_output = f"{status_icon} Exit code {exit_code} ({elapsed_time:.3f}s elapsed)\n\n{output}"
        else:
            formatted_output = f"{status_icon} Exit code {exit_code} ({elapsed_time:.3f}s elapsed)"

        status = ToolResultStatus.SUCCESS if result['success'] else ToolResultStatus.FAILURE
        return SingleToolResult(formatted_output, status=status)
