import os
from dataclasses import dataclass

from .argument_parser import split_arguments
from .base_tool import BaseTool
from ..application.tool_library import ContinueResult


@dataclass
class EditFileArgs:
    filename: str
    edit_mode: str
    start_line: int
    end_line: int
    new_content: str | None


class FileEditor:
    def __init__(self, filename):
        self.filename = filename
        self.lines = []

    def load_file(self):
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f'File "{self.filename}" not found')

        with open(self.filename, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

    def save_file(self):
        with open(self.filename, 'w', encoding='utf-8', newline="\n") as f:
            f.writelines(self.lines)

    def get_indentation(self, line_number):
        if not self.lines or line_number < 1 or line_number > len(self.lines):
            return ""

        line = self.lines[line_number - 1]
        indent = ""
        for char in line:
            if char in [' ', '\t']:
                indent += char
            else:
                break
        return indent

    def normalize_range(self, start_line, end_line):
        total_lines = len(self.lines)
        if total_lines == 0 or end_line < 1 or start_line > total_lines:
            return None

        normalized_start = max(1, start_line)
        normalized_end = min(total_lines, end_line)

        if normalized_start > normalized_end:
            return None

        return normalized_start, normalized_end

    def _trim_terminal_newline(self, new_lines):
        if not self.lines or not new_lines:
            return new_lines
        if self.lines[-1].endswith('\n'):
            return new_lines
        if not new_lines[-1].endswith('\n'):
            return new_lines
        adjusted_lines = new_lines[:]
        adjusted_lines[-1] = adjusted_lines[-1][:-1]
        return adjusted_lines


class InsertMode:
    def apply(self, editor: FileEditor, args: EditFileArgs):
        content = args.new_content

        if content is None:
            new_content = ['\n']
        else:
            inserting_between_lines = args.start_line <= len(editor.lines)
            if not content.endswith('\n') and inserting_between_lines:
                content += '\n'
            new_content = content.splitlines(keepends=True)

        if args.start_line > len(editor.lines):
            if editor.lines and not editor.lines[-1].endswith('\n'):
                editor.lines[-1] += '\n'

            lines_to_add = args.start_line - len(editor.lines) - 1
            if lines_to_add > 0:
                editor.lines.extend(['\n'] * lines_to_add)

            editor.lines.extend(new_content)
        else:
            insert_pos = args.start_line - 1
            editor.lines[insert_pos:insert_pos] = new_content


class DeleteMode:
    def apply(self, editor: FileEditor, args: EditFileArgs):
        normalized_range = editor.normalize_range(args.start_line, args.end_line)
        if normalized_range is None:
            return

        start_line, end_line = normalized_range
        lines_to_delete = set(range(start_line, end_line + 1))
        new_lines = [line for i, line in enumerate(editor.lines, start=1)
                    if i not in lines_to_delete]

        if end_line == len(editor.lines):
            new_lines = editor._trim_terminal_newline(new_lines)

        editor.lines = new_lines


class ReplaceMode:
    def apply(self, editor: FileEditor, args: EditFileArgs):
        # First delete the range
        delete_mode = DeleteMode()
        delete_mode.apply(editor, args)

        # Then insert the new content at the start position
        if args.new_content is not None:
            insert_args = EditFileArgs(
                filename=args.filename,
                edit_mode="insert",
                start_line=args.start_line,
                end_line=args.start_line,
                new_content=args.new_content
            )
            insert_mode = InsertMode()
            insert_mode.apply(editor, insert_args)


class EditFileTool(BaseTool):
    name = "edit-file"
    name = "edit-file"
    description = """Edit files by replacing content in specified line ranges.

CRITICAL FORMATTING RULES:
- Content MUST start on the NEXT line after the command
- End multiline content with 🛠️🔚 marker
- Everything from the next line until 🛠️🔚 is captured as content

Replace mode: First deletes the specified range, then inserts new content at that position."""

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
            "description": "Edit mode: 'replace' (delete range then insert), 'insert', 'delete'"
        },
        {
            "name": "line_range",
            "type": "string",
            "required": True,
            "description": "Line range in format 'start-end' or 'line_number' (e.g., '1-3' or '10' for single line)"
        }
    ]
    examples = [
        "🛠️ edit-file myfile.txt replace 1-3\nHello World\n🛠️🔚",
        "🛠️ edit-file test.txt delete 1",
        "🛠️ edit-file test.txt insert 1\nNew Headline\n🛠️🔚",
        "🛠️ edit-file test.py insert 3\nprint('hello')\n🛠️🔚",
        "🛠️ edit-file test.py replace 5\nnew = 2\n🛠️🔚",
    ]

    def __init__(self):
        self.mode_creators = {
            "insert": InsertMode,
            "delete": DeleteMode,
            "replace": ReplaceMode
        }

    def parse_arguments(self, args):
        if not args:
            return None, 'No arguments specified'

        # Split args into first line and remaining content
        lines = args.splitlines(keepends=True)
        first_line = lines[0].rstrip('\n\r')

        # Parse the command line arguments
        try:
            parts = split_arguments(first_line)
        except ValueError as e:
            return None, f"Error parsing arguments: {str(e)}"

        if len(parts) < 3:
            return None, 'Usage: edit-file <filename> <edit_mode> <line_range>'

        filename, edit_mode, line_range_token = parts[:3]

        # For insert and replace modes, content must be on following lines
        # For delete mode, no content is expected
        if edit_mode in ['insert', 'replace']:
            if len(parts) > 3:
                return None, f'For {edit_mode} mode, content must start on the following line, not on the same line'

            # Extract content from following lines
            if len(lines) > 1:
                new_content = ''.join(lines[1:])
                # Remove trailing newline if it's the only trailing newline
                if new_content.endswith('\n') and not new_content.endswith('\n\n'):
                    new_content = new_content[:-1]
            else:
                new_content = None
        elif edit_mode == 'delete':
            if len(parts) > 3:
                return None, 'Delete mode does not accept content arguments'
            new_content = None
        else:
            return None, f'Invalid edit mode: {edit_mode}. Supported modes: insert, delete, replace'

        try:
            if '-' in line_range_token:
                start_line, end_line = map(int, line_range_token.split('-'))
            else:
                start_line = end_line = int(line_range_token)
        except ValueError:
            return None, 'Invalid line range format. Use format "start-end" (e.g., "1-5")'

        edit_args = EditFileArgs(
            filename=filename,
            edit_mode=edit_mode,
            start_line=start_line,
            end_line=end_line,
            new_content=new_content
        )
        return edit_args, None

    def execute(self, args):
        edit_args, error = self.parse_arguments(args)
        if error or edit_args is None:
            return ContinueResult(error or "Failed to parse arguments")

        try:
            editor = FileEditor(edit_args.filename)
            editor.load_file()

            mode_class = self.mode_creators.get(edit_args.edit_mode)
            if mode_class is None:
                return ContinueResult(
                    f"Invalid edit mode: {edit_args.edit_mode}. Supported modes: insert, delete, replace")

            mode = mode_class()
            mode.apply(editor, edit_args)

            editor.save_file()
            return ContinueResult(f"Successfully edited {edit_args.filename}")

        except FileNotFoundError as e:
            return ContinueResult(str(e))
        except OSError as e:
            return ContinueResult(f'Error editing file "{edit_args.filename}": {str(e)}')
        except Exception as e:
            return ContinueResult(f'Unexpected error editing file "{edit_args.filename}": {str(e)}')
