import os

from simple_agent.application.tool_result import ContinueResult

from .base_tool import BaseTool


class CreateFileTool(BaseTool):
    name = "create-file"
    description = """Create new files with optional content

⚠️ CRITICAL FORMATTING RULES:
- Content starts immediately after the filename on the following lines
- Do NOT add commentary after the tool in the same message
- Everything after the filename until message end is captured as content"""

    arguments = [
        {
            "name": "filename",
            "type": "string",
            "required": True,
            "description": "Path to the file to create (directories will be created automatically)"
        },
        {
            "name": "content",
            "type": "string",
            "required": False,
            "description": "Initial content for the file. Everything after the filename is content!"
        }
    ]
    examples = [
        "🛠️ create-file newfile.txt",
        "🛠️ create-file script.py print(\"Hello World\")",
        "🛠️ create-file multi-line.py This is Line 1\nThis is Line 2",
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args:
            return ContinueResult('No filename specified')

        # Simple string splitting - first word is filename, rest is content
        parts = args.strip().split(None, 1)

        if not parts:
            return ContinueResult('No filename specified')

        filename = parts[0]
        content = parts[1] if len(parts) > 1 else None

        if content == '':
            content = None

        try:
            # Check if file already exists
            if os.path.exists(filename):
                return ContinueResult(f"Error creating file '{filename}': File already exists")

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

            with open(filename, 'w', encoding='utf-8', newline='\n') as f:
                if content is not None:
                    # Write content as-is, no processing
                    f.write(content)
            if content is not None:
                return ContinueResult(f"Created file: {filename} with content")
            else:
                return ContinueResult(f"Created empty file: {filename}")
        except OSError as e:
            return ContinueResult(f"Error creating file '{filename}': {str(e)}")
        except Exception as e:
            return ContinueResult(f"Unexpected error creating file '{filename}': {str(e)}")
