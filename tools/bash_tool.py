import subprocess

from .base_tool import BaseTool

class BashTool(BaseTool):
    name = 'bash'
    description = "Execute bash commands"
    arguments = [
        {
            "name": "command",
            "type": "string",
            "required": True,
            "description": "The bash command to execute"
        }
    ]
    examples = [
        "🛠️ bash echo hello",
        "🛠️ bash ls -la",
        "🛠️ bash pwd"
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args:
            return 'STDERR: bash: missing command'

        _ = subprocess
        result = self.runcommand("bash", ["-c", args])
        return result['output']
