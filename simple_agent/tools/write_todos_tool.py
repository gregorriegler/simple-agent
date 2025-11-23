from pathlib import Path

from simple_agent.application.tool_library import ContinueResult

from .base_tool import BaseTool


class WriteTodosTool(BaseTool):
    name = "write-todos"
    description = "Organize your work in TODOs. Use this tool to create or update those TODOs"
    arguments = [
        {
            "name": "content",
            "type": "string",
            "required": True,
            "description": "Markdown checklist to represent the todos. Use - [ ] for todo, - [ ] **doing** for in-progress, - [x] for done"
        }
    ]
    examples = [
        "🛠️ write-todos\n- [ ] Item 1\n🛠️🔚",
        "🛠️ write-todos\n- [ ] Feature exploration\n- [ ] **Implementing tool**\n- [x] Initial setup\n🛠️🔚"
    ]

    def __init__(self, file_identifier: str):
        super().__init__()
        self.file_identifier = file_identifier

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult("No todo content provided", success=False)
        content = args
        path = Path(f".{self.file_identifier}.todos.md")
        path.write_text(content, encoding="utf-8")
        return ContinueResult("Updated TODOS")
