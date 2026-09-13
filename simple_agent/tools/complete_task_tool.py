from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult, ToolResultStatus
from .base_tool import BaseTool


class CompleteTaskTool(BaseTool):
    name = "complete-task"
    description = (
        "Deliver your final answer to the user and end your turn. "
        "The answer is shown to the user verbatim. Write it as if replying directly: "
        "the result, what you did, and anything they need to know."
    )
    arguments = ToolArguments(
        header=[
            ToolArgument(
                name="answer",
                type="string",
                required=True,
                description="Your complete final answer, shown to the user as-is",
            )
        ]
    )
    examples = [
        {
            "answer": "Created the user registration system. Sign-up now validates emails."
        },
        {
            "answer": "Fixed the rounding bug in payment processing; totals match the invoice."
        },
    ]

    async def execute(self, call):
        args = str(call.named_arguments.get("answer", ""))
        if not args or not args.strip():
            return SingleToolResult(
                "STDERR: complete-task: missing answer",
                status=ToolResultStatus.FAILURE,
                completes=True,
            )
        answer = args.strip()
        return SingleToolResult(answer, completes=True)
