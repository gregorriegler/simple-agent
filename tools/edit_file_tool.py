from .base_tool import BaseTool
import os
from dataclasses import dataclass

@dataclass
class EditFileArgs:
    filename: str
    edit_mode: str
    start_line: int
    end_line: int
    new_content: str | None

class EditFileTool(BaseTool):
    name = "edit-file"
    description = "Edit files by replacing content in specified line ranges"
    arguments = [
        {
            "name": "filename",
            "type": "string",
            "required": True,
            "description": "Path to the file to edit"
        },
        {
            "name": "edit_mode",
            "type": "string",
            "required": True,
            "description": "Edit mode ('replace', 'insert', 'delete')"
        },
        {
            "name": "line_range",
            "type": "string",
            "required": True,
            "description": "Line range in format 'start-end' or 'line_number' (e.g., '1-3' or '10' for single line)"
        },
        {
            "name": "new_content",
            "type": "string",
            "required": False,
            "description": "New content to replace the specified lines."
        }
    ]
    examples = [
        "🛠️ edit-file myfile.txt replace 1-3 Hello World",
        "to delete the first line\n🛠️ edit-file test.txt 1-1",
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def _parse_arguments(self, args):
        if not args:
            return None, 'No arguments specified'

        parts = args.split(' ', 3)
        if len(parts) < 3:
            return None, 'Usage: edit-file <filename> <edit_mode> <line_range> [new_content]'

        try:
            line_range = parts[2]
            if '-' in line_range:
                start_line, end_line = map(int, line_range.split('-'))
            else:
                start_line = end_line = int(parts[2])
            new_content = parts[3] if len(parts) > 3 else None

            edit_args = EditFileArgs(
                filename=parts[0],
                edit_mode=parts[1],
                start_line=start_line,
                end_line=end_line,
                new_content=new_content
            )
            return edit_args, None
        except ValueError:
            return None, 'Invalid line range format. Use format "start-end" (e.g., "1-5")'

    def _validate_line_range(self, start_line, end_line, total_lines):
        """Validate that the line range is valid for the file."""
        # Special case: allow 0-0 for empty files (append mode)
        if total_lines == 0:
            return None

        if start_line < 1 or end_line < 1 or start_line > total_lines or end_line > total_lines:
            return f"Invalid line range: {start_line} {end_line} for file with {total_lines} lines"

        if start_line > end_line:
            return f"Start line ({start_line}) cannot be greater than end line ({end_line})"

        return None

    def execute(self, args):
        edit_args, error = self._parse_arguments(args)
        if error:
            return error

        return self._perform_file_edit(edit_args)


    def _perform_file_edit(self, edit_args):
        try:
            if not os.path.exists(edit_args.filename):
                return f'File "{edit_args.filename}" not found'

            with open(edit_args.filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            validation_error = self._validate_line_range(edit_args.start_line, edit_args.end_line, len(lines))
            if validation_error:
                return validation_error

            if edit_args.edit_mode == "insert":
                new_content = edit_args.new_content.splitlines(keepends=True)
                lines[edit_args.start_line-1:edit_args.start_line-1] = new_content
                new_lines = lines
            if edit_args.edit_mode == "replace":
                if len(lines) == 0 and edit_args.start_line == 0 and edit_args.end_line == 0:
                    if edit_args.new_content is None:
                        new_lines = []
                    elif '\n' in edit_args.new_content:
                        new_lines = [line + '\n' for line in edit_args.new_content.split('\n') if line]
                    else:
                        new_lines = [edit_args.new_content + '\n']
                else:
                    # Convert to 0-based indexing
                    start_idx = edit_args.start_line - 1
                    end_idx = edit_args.end_line - 1

                    # Handle deletion or replacement
                    if edit_args.new_content is None:
                        # Delete lines
                        replacement_lines = []
                    elif '\n' in edit_args.new_content:
                        replacement_lines = [line + '\n' for line in edit_args.new_content.split('\n') if line]
                    else:
                        # For single-line content, preserve the original line ending behavior
                        last_replaced_line = lines[end_idx] if end_idx < len(lines) else ''
                        if last_replaced_line.endswith('\n'):
                            replacement_lines = [edit_args.new_content + '\n']
                        else:
                            replacement_lines = [edit_args.new_content]

                    new_lines = lines[:start_idx] + replacement_lines + lines[end_idx + 1:]

            # Write back to file
            with open(edit_args.filename, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            return f"Successfully edited {edit_args.filename}"

        except OSError as e:
            return f'Error editing file "{edit_args.filename}": {str(e)}'
        except Exception as e:
            return f'Unexpected error editing file "{edit_args.filename}": {str(e)}'
