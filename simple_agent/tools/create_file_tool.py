import os

from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult, ToolResultStatus

from .base_tool import BaseTool


class CreateFileTool(BaseTool):
    name = "create-file"
    description = "Create new files with optional content. You cannot overwrite an existing file. In that case you have to first remove it."
    arguments = ToolArguments(
        header=[
            ToolArgument(
                name="filename",
                type="string",
                required=True,
                description="Path to the file to create (directories will be created automatically)",
            ),
        ],
        body=ToolArgument(
            name="content",
            type="string",
            required=False,
            description="Initial content for the file. Everything after the filename is content!",
        ),
    )
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
            "result": "Created empty file: newfile.txt",
        },
        {"filename": "script.py", "content": 'print("Hello World")'},
        {"filename": "multi-line.py", "content": "Line 1\nLine 2"},
    ]

    async def execute(self, raw_call):
        args = raw_call.arguments
        body = raw_call.body

        if not args:
            return SingleToolResult(
                "No filename specified", status=ToolResultStatus.FAILURE
            )

        # Simple string splitting - first word is filename
        parts = args.strip().split(None, 1)

        if not parts:
            return SingleToolResult(
                "No filename specified", status=ToolResultStatus.FAILURE
            )

        filename = parts[0]
        content = body if body else None

        try:
            # Check if file already exists
            if os.path.exists(filename):
                return SingleToolResult(
                    f"Error creating file '{filename}': File already exists",
                    status=ToolResultStatus.FAILURE,
                )

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

            with open(filename, "w", encoding="utf-8", newline="\n") as f:
                if content is not None:
                    # Write content as-is, no processing
                    f.write(content)
            if content is not None:
                return SingleToolResult(
                    f"Created file: {filename} with content", display_body=content
                )
            else:
                return SingleToolResult(f"Created empty file: {filename}")
        except OSError as e:
            return SingleToolResult(
                f"Error creating file '{filename}': {str(e)}",
                status=ToolResultStatus.FAILURE,
            )
        except Exception as e:
            return SingleToolResult(
                f"Unexpected error creating file '{filename}': {str(e)}",
                status=ToolResultStatus.FAILURE,
            )
