from ..application.tool_library import ContinueResult, ToolArgument, ToolArguments
from .base_tool import BaseTool
import os

class EditFileTool(BaseTool):
    name = "edit-file"
    description = """Edits a file by replacing a search block with a replacement block.

This tool can be used to insert, delete, or replace content in a file.

- To **replace** content, provide the old content in the SEARCH block and the new content in the REPLACE block.
- To **insert** content, provide the line to insert after in the SEARCH block, and in the REPLACE block, provide the same line followed by the new content.
- To **delete** content, provide the content to be deleted in the SEARCH block and leave the REPLACE block empty.
"""
    arguments = ToolArguments(header=[
        ToolArgument(
            name="filename",
            type="string",
            required=True,
            description="Path to the file to edit",
        ),
    ], body=ToolArgument(
        name="edit_block",
        type="string",
        required=True,
        description="""A block of text containing the content to search for and the content to replace it with, formatted as follows:
<<<<<<< SEARCH
... content to search for ...
=======
... new content to insert ...
>>>>>>> REPLACE
""",
    ))
    examples = [
        {
            "filename": "myfile.txt",
            "edit_block": """<<<<<<< SEARCH
Hello, world!
=======
Hello, universe!
>>>>>>> REPLACE
""",
        },
    ]

    def execute(self, raw_call):
        filename = raw_call.arguments
        edit_block = raw_call.body

        if not filename:
            return ContinueResult("Filename not specified.", success=False)

        if not edit_block:
            return ContinueResult("Edit block not specified.", success=False)

        try:
            search_content, replace_content = self._parse_edit_block(edit_block)
        except ValueError as e:
            return ContinueResult(str(e), success=False)

        if not search_content:
            return ContinueResult("SEARCH content cannot be empty.", success=False)

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except FileNotFoundError:
            return ContinueResult(f'File not found: "{filename}"', success=False)
        except Exception as e:
            return ContinueResult(f'Error reading file "{filename}": {str(e)}', success=False)

        if search_content not in original_content:
            return ContinueResult("The SEARCH content was not found in the file.", success=False)

        new_content = original_content.replace(search_content, replace_content, 1)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            return ContinueResult(f'Error writing to file "{filename}": {str(e)}', success=False)

        return ContinueResult(f'Successfully edited "{filename}".')

    def _parse_edit_block(self, edit_block):
        lines = edit_block.splitlines(keepends=True)

        if not lines or lines[0].strip() != '<<<<<<< SEARCH':
            raise ValueError("Invalid format: Block must start with '<<<<<<< SEARCH'")

        if lines[-1].strip() != '>>>>>>> REPLACE':
            raise ValueError("Invalid format: Block must end with '>>>>>>> REPLACE'")

        separator_index = -1
        for i, line in enumerate(lines):
            if line.strip() == '=======':
                separator_index = i
                break

        if separator_index == -1:
            raise ValueError("Invalid format: Missing '=======' separator")

        search_lines = lines[1:separator_index]
        replace_lines = lines[separator_index + 1:-1]

        # Reconstruct content, preserving original line endings
        search_content = "".join(search_lines)
        replace_content = "".join(replace_lines)

        return search_content, replace_content
