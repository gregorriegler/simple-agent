from pathlib import Path

from simple_agent.application.tool_library import ContinueResult

from .base_tool import BaseTool, ToolArgument


class WriteTodosTool(BaseTool):
    name = "write-todos"
    description = "Organize your work in TODOs. Use this tool to create or update those TODOs"
    arguments = [
        ToolArgument(
            name="content",
            type="string",
            required=True,
            multiline=True,
            description="Markdown checklist to represent the todos. Use - [ ] for todo, - [ ] **doing** for in-progress, - [x] for done",
        )
    ]
    examples = [
        {"content": "- [ ] Item 1\n"},
        {"content": "- [ ] Feature exploration\n- [ ] **Implementing tool**\n- [x] Initial setup"},
    ]

    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult("No todo content provided", success=False)
        content = args
        path = Path(self.filename)
        path.write_text(content, encoding="utf-8")
        return ContinueResult("Updated TODOS")
