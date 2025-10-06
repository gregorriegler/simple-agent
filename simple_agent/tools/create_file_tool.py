import os

from simple_agent.application.tool_result import ContinueResult

from .argument_parser import create_lexer, split_arguments
from .base_tool import BaseTool


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
            return ContinueResult('No filename specified')

        try:
            tokens = split_arguments(args)
        except ValueError as e:
            return ContinueResult(f"Error parsing arguments: {str(e)}")

        if not tokens:
            return ContinueResult('No filename specified')

        filename = tokens[0]

        # Extract content: everything after the filename using lexer approach
        lexer = create_lexer(args)

        try:
            lexer.get_token()  # Get filename token
        except ValueError as e:
            return ContinueResult(f"Error parsing arguments: {str(e)}")

        # Get the remainder of the input after the filename
        remainder = ''
        if lexer.instream:
            # Read all remaining characters from the stream
            while True:
                try:
                    char = lexer.instream.read(1)
                    if not char:
                        break
                    remainder += char
                except:
                    break

        content = remainder.lstrip() if remainder else None

        if content == '':
            content = None

        # Handle quoted content properly - remove outer quotes if they match
        if content and len(content) >= 2:
            if ((content.startswith('"') and content.endswith('"')) or
                (content.startswith("'") and content.endswith("'"))):
                content = content[1:-1]

        try:
            # Check if file already exists
            if os.path.exists(filename):
                return ContinueResult(f"Error creating file '{filename}': File already exists")

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

            with open(filename, 'w', encoding='utf-8', newline='\n') as f:
                if content is not None:
                    # Process escape sequences properly - use a more robust approach
                    # First handle double backslashes, then specific escape sequences
                    processed_content = content
                    # Replace \\n, \\t, \\r with actual escape sequences, but preserve literal backslashes
                    processed_content = processed_content.replace('\\\\', '\x00TEMP_BACKSLASH\x00')  # Temporary placeholder
                    processed_content = processed_content.replace('\\n', '\n')
                    processed_content = processed_content.replace('\\t', '\t')
                    processed_content = processed_content.replace('\\r', '\r')
                    processed_content = processed_content.replace('\x00TEMP_BACKSLASH\x00', '\\')  # Restore literal backslashes
                    f.write(processed_content)
            if content is not None:
                return ContinueResult(f"Created file: {filename} with content")
            else:
                return ContinueResult(f"Created empty file: {filename}")
        except OSError as e:
            return ContinueResult(f"Error creating file '{filename}': {str(e)}")
        except Exception as e:
            return ContinueResult(f"Unexpected error creating file '{filename}': {str(e)}")
