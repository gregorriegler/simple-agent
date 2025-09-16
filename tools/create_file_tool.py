from .base_tool import BaseTool
from .argument_parser import create_lexer, split_arguments
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
        "🛠️ create-file newfile.txt",
        "🛠️ create-file script.py print(\"Hello World\")"
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def execute(self, args):
        if not args:
            return 'No filename specified'

        try:
            tokens = split_arguments(args)
        except ValueError as e:
            return f"Error parsing arguments: {str(e)}"

        if not tokens:
            return 'No filename specified'

        lexer = create_lexer(args)

        try:
            lexer.get_token()
        except ValueError as e:
            return f"Error parsing arguments: {str(e)}"

        remainder = lexer.instream.read() if lexer.instream else ''
        content = remainder.lstrip() if remainder else None

        if content == '':
            content = None

        if content and content.startswith('"') and content.endswith('"'):
            content = content[1:-1]

        filename = tokens[0]

        try:
            # Check if file already exists
            if os.path.exists(filename):
                return f"Error creating file '{filename}': File already exists"

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

            with open(filename, 'w', encoding='utf-8') as f:
                if content is not None:
                    # Process escape sequences like \n
                    processed_content = content.encode().decode('unicode_escape')
                    f.write(processed_content)
            if content is not None:
                return f"Created file: {filename} with content"
            else:
                return f"Created empty file: {filename}"
        except OSError as e:
            return f"Error creating file '{filename}': {str(e)}"
        except Exception as e:
            return f"Unexpected error creating file '{filename}': {str(e)}"
