from pathlib import Path

from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus

from .base_tool import BaseTool


class CommunicateIntentTool(BaseTool):
    name = "communicate-intent"
    description = (
        "State your current overarching goal (e.g. implementing a feature, "
        "investigating a failure, or fixing a bug) so an observer knows what "
        "you are working toward. Do NOT call this for individual steps, tool "
        "executions, running tests, or committing changes. Only call it when "
        "the high-level pursuit changes."
    )
    arguments = ToolArguments(
        header=[],
        body=ToolArgument(
            name="intent",
            type="string",
            required=True,
            description="A single short sentence describing the current goal",
        ),
    )
    examples = [
        {
            "intent": "Extract the tool syntax parser",
            "result": "Intent: Extract the tool syntax parser",
        }
    ]

    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    async def execute(self, raw_call):
        body = raw_call.body
        if not body or not body.strip():
            return SingleToolResult(
                "No intent provided", status=ToolResultStatus.FAILURE
            )

        intent = body.strip()
        Path(self.filename).write_text(intent, encoding="utf-8")
        return SingleToolResult(f"Intent: {intent}")
