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
        "/ls",
        "/ls /home/user"
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, path="."):
        return self.runcommand("ls", ["-a", path] if path else ["-a"])
