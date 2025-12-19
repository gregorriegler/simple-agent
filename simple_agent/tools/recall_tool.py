from pathlib import Path

from ..application.tool_library import ToolArguments
from ..application.tool_results import ContinueResult

from .base_tool import BaseTool


class RecallTool(BaseTool):
    name = "recall"
    description = "Retrieve all stored memories from .memory.md"
    arguments = ToolArguments()
    examples = [
        {}
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    async def execute(self, raw_call):
        path = Path(".memory.md")

        if not path.exists():
            return ContinueResult("No memories stored yet")

        content = path.read_text(encoding="utf-8")
        return ContinueResult(f"Memories:\n{content}")
