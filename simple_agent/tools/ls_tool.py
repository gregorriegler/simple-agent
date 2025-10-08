from simple_agent.application.tool_result import ContinueResult
from .base_tool import BaseTool
class LsTool(BaseTool):
    name = "ls"
    description = "List directory contents with detailed information"
    arguments = [
        {
            "name": "path",
            "type": "string",
            "required": False,
            "description": "Directory path to list (defaults to current directory)"
        }
    ]
    examples = [
        "🛠️ ls",
        "🛠️ ls /home/user"
    ]

    def execute(self, path="."):
        result = self.run_command("ls", ["-a", path] if path else ["-a"])
        return ContinueResult(result['output'])
