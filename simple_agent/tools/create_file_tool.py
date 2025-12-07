import os

from ..application.tool_library import ContinueResult, ToolArgument

from .base_tool import BaseTool


class CreateFileTool(BaseTool):
    name = "create-file"
    description = """Create new files with optional content

- End content with 🛠️🔚 marker
- Do NOT add commentary after the tool in the same message
- Everything after the filename until 🛠️🔚 or message end is captured as content"""

    arguments = [
        ToolArgument(
            name="filename",
            type="string",
            required=True,
            description="Path to the file to create (directories will be created automatically)",
        ),
        ToolArgument(
            name="content",
            type="string",
            required=False,
            multiline=True,
            description="Initial content for the file. Everything after the filename is content!",
        ),
    ]
    examples = [
        {"filename": "newfile.txt", "content": ""},
        {"filename": "script.py", "content": "print(\"Hello World\")"},
        {"filename": "multi-line.py", "content": "Line 1\nLine 2"},
    ]

    def execute(self, args):
        if not args:
            return ContinueResult('No filename specified', success=False)

        # Simple string splitting - first word is filename, rest is content
        parts = args.strip().split(None, 1)

        if not parts:
            return ContinueResult('No filename specified', success=False)

        filename = parts[0]
        content = parts[1] if len(parts) > 1 else None

        if content == '':
            content = None

        try:
            # Check if file already exists
            if os.path.exists(filename):
                return ContinueResult(f"Error creating file '{filename}': File already exists", success=False)

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)

            with open(filename, 'w', encoding='utf-8', newline='\n') as f:
                if content is not None:
                    # Write content as-is, no processing
                    f.write(content)
            if content is not None:
                return ContinueResult(f"Created file: {filename} with content", display_body=content)
            else:
                return ContinueResult(f"Created empty file: {filename}")
        except OSError as e:
            return ContinueResult(f"Error creating file '{filename}': {str(e)}", success=False)
        except Exception as e:
            return ContinueResult(f"Unexpected error creating file '{filename}': {str(e)}", success=False)
