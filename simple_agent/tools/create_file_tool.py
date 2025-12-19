import os

from ..application.tool_library import ContinueResult, ToolArgument, ToolArguments

from .base_tool import BaseTool


class CreateFileTool(BaseTool):
    name = "create-file"
    description = "Create new files with optional content"
    arguments = ToolArguments(header=[
        ToolArgument(
            name="filename",
            type="string",
            required=True,
            description="Path to the file to create (directories will be created automatically)",
        ),
    ], body=ToolArgument(
        name="content",
        type="string",
        required=False,
        description="Initial content for the file. Everything after the filename is content!",
    ))
    body = ToolArgument(
        name="content",
        type="string",
        required=False,
        description="Initial content for the file. Everything after the filename is content!",
    )
    examples = [
        {
            "reasoning": "I need to create an empty file for later use.",
            "filename": "newfile.txt",
            "content": "",
            "result": "Created empty file: newfile.txt"
        },
        {"filename": "script.py", "content": "print(\"Hello World\")"},
        {"filename": "multi-line.py", "content": "Line 1\nLine 2"},
    ]

    async def execute(self, raw_call):
        args = raw_call.arguments
        body = raw_call.body

        if not args:
            return ContinueResult('No filename specified', success=False)

        # Simple string splitting - first word is filename
        parts = args.strip().split(None, 1)

        if not parts:
            return ContinueResult('No filename specified', success=False)

        filename = parts[0]
        content = body if body else None

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
