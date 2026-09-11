from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus

from .base_tool import BaseTool


class SuggestTool(BaseTool):
    name = "suggest"
    description = (
        "Propose a change to the agent you are observing. "
        "Only call it when you have something to propose - "
        "complete your task without suggesting when the change looks fine."
    )
    arguments = ToolArguments(
        header=[],
        body=ToolArgument(
            name="suggestion",
            type="string",
            required=True,
            description="The proposed change and a short reason for it",
        ),
    )
    examples = [
        {
            "suggestion": "data1.txt says nothing about its content, call it greeting.txt",
            "result": "Suggested: data1.txt says nothing about its content, call it greeting.txt",
        }
    ]

    async def execute(self, call):
        body = str(call.named_arguments.get("suggestion", ""))
        if not body or not body.strip():
            return SingleToolResult(
                "No suggestion provided", status=ToolResultStatus.FAILURE
            )
        return SingleToolResult(f"Suggested: {body.strip()}")
