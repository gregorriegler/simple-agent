from .base_tool import BaseTool
import os

class CreateFileTool(BaseTool):
    name = "create"
    description = "Create new empty files"

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args:
            return {'success': False, 'output': 'No filename specified', 'returncode': 1}
        
        parts = args.split(' ', 1)  # Split into at most 2 parts: filename and content
        filename = parts[0]
        content = parts[1] if len(parts) > 1 else None
        
        try:
            with open(filename, 'w') as f:
                if content is not None:
                    f.write(content)
            if content is not None:
                return {'success': True, 'output': f"Created file: {filename} with content", 'returncode': 0}
            else:
                return {'success': True, 'output': f"Created empty file: {filename}", 'returncode': 0}
        except Exception as e:
            return {'success': False, 'output': f"Error creating file '{filename}': {str(e)}", 'returncode': 1}