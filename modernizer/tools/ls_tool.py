from .base_tool import BaseTool


class LsTool(BaseTool):
    name = "ls"
    description = "List directory contents with detailed information"

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, path="."):
        return self.runcommand("ls", ["-a", path] if path else ["-a"])
