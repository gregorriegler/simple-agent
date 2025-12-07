from pathlib import Path

from ..application.tool_library import ContinueResult, ToolArgument

from .base_tool import BaseTool


class RememberTool(BaseTool):
    name = "remember"
    description = "Store a memory to .memory.md for later recall"
    arguments = [
        ToolArgument(
            name="content",
            type="string",
            required=True,
            description="The memory content to store",
        )
    ]
    examples = [
        {"content": "The user prefers Python over JavaScript"},
        {"content": "API key format: sk-proj-xxxxx"},
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult("No memory content provided", success=False)

        content = args.strip()
        path = Path(".memory.md")

        if path.exists():
            existing_content = path.read_text(encoding="utf-8")
            new_content = f"{existing_content}\n- {content}\n"
        else:
            new_content = f"# Memories\n\n- {content}\n"

        path.write_text(new_content, encoding="utf-8")
        return ContinueResult(f"Remembered: {content}")
