from ..application.tool_library import CompleteResult, ToolArgument, ToolArguments
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

    def execute(self, raw_call):
        args = raw_call.arguments
        if not args or not args.strip():
            return CompleteResult('STDERR: complete-task: missing summary', success=False)
        summary = args.strip()
        return CompleteResult(summary)

