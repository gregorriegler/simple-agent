from pathlib import Path

from simple_agent.application.tool_result import ContinueResult

from .base_tool import BaseTool


class WriteTodosTool(BaseTool):
    name = "WriteTodos"
    description = "Create or update .todos.md with provided markdown content"
    arguments = [
        {
            "name": "content",
            "type": "string",
            "required": True,
            "description": "Markdown text to write into .todos.md"
        }
    ]
    examples = [
        "🛠️ WriteTodos ## Todo\\n- Item 1",
        "🛠️ WriteTodos\\n## Todo\\n- Feature exploration\\n\\n## Doing\\n- Implementing tool\\n\\n## Done\\n- Initial setup"
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult("No todo content provided")
        content = args
        path = Path(".todos.md")
        path.write_text(content, encoding="utf-8")
        return ContinueResult("Updated .todos.md")
