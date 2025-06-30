from .base_tool import BaseTool
import os

class CreateFileTool(BaseTool):
    name = "create"
    description = "Create new empty files"

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, filename):
        try:
            # Create empty file using Python's built-in operations
            with open(filename, 'w') as f:
                pass  # Creates empty file
            return {'success': True, 'output': f"Created empty file: {filename}", 'returncode': 0}
        except Exception as e:
            return {'success': False, 'output': f"Error creating file '{filename}': {str(e)}", 'returncode': 1}