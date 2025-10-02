from application.tool_result import CompleteResult
from .base_tool import BaseTool
class CompleteTaskTool(BaseTool):
    name = "complete-task"
    description = "Signal task completion with a summary of what was accomplished"
    arguments = [
        {
            "name": "summary",
            "type": "string",
            "required": True,
            "description": "Final summary of what was accomplished"
        }
    ]
    examples = [
        "🛠️ complete-task Successfully created the user registration system",
        "🛠️ complete-task Fixed the bug in the payment processing module"
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args or not args.strip():
            return CompleteResult('STDERR: complete-task: missing summary')
        summary = args.strip()
        return CompleteResult(summary)

