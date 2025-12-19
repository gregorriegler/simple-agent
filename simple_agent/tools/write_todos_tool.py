from pathlib import Path

from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.application.tool_results import ContinueResult

from .base_tool import BaseTool


class WriteTodosTool(BaseTool):
    name = "write-todos"
    description = "Organize your work in TODOs. Use this tool to create or update those TODOs"
    arguments = ToolArguments(
        header=[],
        body=ToolArgument(
            name="content",
            type="string",
            required=True,
            description="Markdown checklist to represent the todos. Use - [ ] for todo, - [ ] **doing** for in-progress, - [x] for done",
        )
    )
    examples = [
        {
            "content": "- [ ] Item 1",
            "result": "Updated TODOS"
        },
        {"content": "- [ ] Feature exploration\n- [ ] **Implementing tool**\n- [x] Initial setup"},
    ]

    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    async def execute(self, raw_call):
        body = raw_call.body
        if not body or not body.strip():
            return ContinueResult("No todo content provided", success=False)

        content = body

        path = Path(self.filename)
        path.write_text(content, encoding="utf-8")
        return ContinueResult("Updated TODOS")
