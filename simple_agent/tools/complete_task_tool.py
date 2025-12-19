from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult, ToolResultStatus
from .base_tool import BaseTool


class CompleteTaskTool(BaseTool):
    name = "complete-task"
    description = "Signal task completion with a summary of what was accomplished"
    arguments = ToolArguments(header=[
        ToolArgument(
            name="summary",
            type="string",
            required=True,
            description="Final summary of what was accomplished",
        )
    ])
    examples = [
        {"summary": "Successfully created the user registration system"},
        {"summary": "Fixed the bug in the payment processing module"},
    ]

    async def execute(self, raw_call):
        args = raw_call.arguments
        if not args or not args.strip():
            return SingleToolResult('STDERR: complete-task: missing summary', status=ToolResultStatus.FAILURE, completes=True)
        summary = args.strip()
        return SingleToolResult(summary, completes=True)
