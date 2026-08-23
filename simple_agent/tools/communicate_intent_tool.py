from pathlib import Path

from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus

from .base_tool import BaseTool


class CommunicateIntentTool(BaseTool):
    name = "communicate-intent"
    description = (
        "Communicate what you are currently trying to achieve. "
        "This is state, not a log: a new call overwrites the previous intent. "
        "Call it when your goal changes, not on every step."
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
