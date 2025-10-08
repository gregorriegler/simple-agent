from pathlib import Path

from simple_agent.application.tool_result import ContinueResult

from .base_tool import BaseTool


class WriteTodosTool(BaseTool):
    name = "write-todos"
    description = "Organize your work in TODOs. Use this tool to create or update those TODOs"
    arguments = [
        {
            "name": "content",
            "type": "string",
            "required": True,
            "description": "Markdown text to represent the todos"
        }
    ]
    examples = [
        "🛠️ write-todos ## Todo\\n- Item 1",
        "🛠️ write-todos\\n## Todo\\n- Feature exploration\\n\\n## Doing\\n- Implementing tool\\n\\n## Done\\n- Initial setup"
    ]

    def __init__(self, agent_id="Agent"):
        super().__init__()
        self.agent_id = agent_id

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult("No todo content provided")
        content = args
        path = Path(f".{self.agent_id}.todos.md")
        path.write_text(content, encoding="utf-8")
        return ContinueResult("Updated TODOS")
