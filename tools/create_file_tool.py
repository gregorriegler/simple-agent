from .base_tool import BaseTool
import os

class CreateFileTool(BaseTool):
    name = "create-file"
    description = "Create new files with optional content"
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
            "description": "Initial content for the file (supports \\n for newlines)"
        }
    ]
    examples = [
        "/create-file newfile.txt",
        "/create-file script.py print(\"Hello World\")"
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args:
            return {'success': False, 'output': 'No filename specified', 'returncode': 1}

        parts = args.split(' ', 1)  # Split into at most 2 parts: filename and content
        filename = parts[0]
        content = parts[1] if len(parts) > 1 else None

        # Remove surrounding quotes from filename if present
        if filename.startswith('"') and filename.endswith('"'):
            filename = filename[1:-1]

        # Remove surrounding quotes from content if present
        if content and content.startswith('"') and content.endswith('"'):
            content = content[1:-1]

        try:
            # Check if file already exists
            if os.path.exists(filename):
                return {'success': False, 'output': f"Error creating file '{filename}': File already exists", 'returncode': 1}

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

            with open(filename, 'w', encoding='utf-8') as f:
                if content is not None:
                    # Process escape sequences like \n
                    processed_content = content.encode().decode('unicode_escape')
                    f.write(processed_content)
            if content is not None:
                return {'success': True, 'output': f"Created file: {filename} with content", 'returncode': 0}
            else:
                return {'success': True, 'output': f"Created empty file: {filename}", 'returncode': 0}
        except OSError as e:
            return {'success': False, 'output': f"Error creating file '{filename}': {str(e)}", 'returncode': 1}
        except Exception as e:
            return {'success': False, 'output': f"Unexpected error creating file '{filename}': {str(e)}", 'returncode': 1}
