import difflib
import os
from dataclasses import dataclass
from enum import Enum

from .argument_parser import split_arguments
from .base_tool import BaseTool
from ..application.tool_library import ContinueResult, ToolArgument, ToolArguments


class EditMode(Enum):
    INSERT = "insert"
    DELETE = "delete"
    DELETE_LINES_THEN_INSERT = "delete_lines_then_insert"


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
        self.original_lines = []

    def load_file(self):
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f'File "{self.filename}" not found')

        with open(self.filename, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
        self.original_lines = self.lines[:]

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

    def build_diff(self):
        diff_lines = list(
            difflib.unified_diff(
                self.original_lines,
                self.lines,
                fromfile=f"{self.filename} (original)",
                tofile=f"{self.filename} (updated)",
            )
        )
        return diff_lines


class InsertMode:
    mode = EditMode.INSERT
    requires_content = False
    allows_content = True

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
    mode = EditMode.DELETE
    requires_content = False
    allows_content = False

    def apply(self, editor: FileEditor, args: EditFileArgs):
        normalized_range = editor.normalize_range(args.start_line, args.end_line)
        if normalized_range is None:
            return

        start_line, end_line = normalized_range
        lines_to_delete = set(range(start_line, end_line + 1))
        new_lines = []

        for i, line in enumerate(editor.lines, start=1):
            if i in lines_to_delete:
                continue
            new_lines.append(line)

        editor.lines = new_lines


class DeleteLinesThenInsertMode:
    mode = EditMode.DELETE_LINES_THEN_INSERT
    requires_content = False
    allows_content = True

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
    description = "Edit files using line-based operations: insert, delete, or delete_lines_then_insert. Careful, whenever you make line-altering edits, the line numbers of subsequent lines will change."

    arguments = ToolArguments(header=[
        ToolArgument(
            name="filename",
            type="string",
            required=True,
            description="Path to the file to edit",
        ),
        ToolArgument(
            name="edit_mode",
            type="string",
            required=True,
            description="Edit mode: 'insert', 'delete', 'delete_lines_then_insert'",
        ),
        ToolArgument(
            name="line_range",
            type="string",
            required=True,
            description="Line range in format 'start-end' or 'line_number' (e.g., '1-3' or '10' for single line)",
        ),
    ], body=ToolArgument(
        name="content",
        type="string",
        required=False,
        description="Optional content for insert/delete_lines_then_insert operations",
    ))
    examples = [
        {"filename": "test.txt", "edit_mode": "delete", "line_range": "1"},
        {"filename": "test.py", "edit_mode": "insert", "line_range": "3", "content": "print('hello')"},
        {"filename": "myfile.txt", "edit_mode": "delete_lines_then_insert", "line_range": "1-3", "content": "Hello World"},
        {"filename": "test.py", "edit_mode": "delete_lines_then_insert", "line_range": "5", "content": "new = 2"},
    ]

    MODE_CLASSES = [
        InsertMode,
        DeleteMode,
        DeleteLinesThenInsertMode,
    ]

    def __init__(self):
        self.modes = {cls.mode.value: cls for cls in self.MODE_CLASSES}

    def execute(self, raw_call):
        edit_args, error = self.parse_arguments(raw_call)
        if error or edit_args is None:
            return ContinueResult(error or "Failed to parse arguments", success=False)

        try:
            editor = FileEditor(edit_args.filename)
            editor.load_file()

            mode_class = self.modes.get(edit_args.edit_mode)
            if mode_class is None:
                valid_modes = ", ".join(self.modes.keys())
                return ContinueResult(
                    f"Invalid edit mode: {edit_args.edit_mode}. Supported modes: {valid_modes}", success=False)

            mode = mode_class()
            mode.apply(editor, edit_args)

            diff_lines = editor.build_diff()

            editor.save_file()

            if diff_lines:
                diff_message = self._format_diff(diff_lines)
                summary = f"Successfully edited {edit_args.filename}"
                message = f"{summary}\n\n{diff_message}"
                return ContinueResult(
                    message,
                    display_body=diff_message,
                    display_language="diff",
                )

            summary = f"No changes made to {edit_args.filename}"
            return ContinueResult(
                summary,
                display_body=summary,
            )

        except FileNotFoundError as e:
            return ContinueResult(str(e), success=False)
        except OSError as e:
            return ContinueResult(f'Error editing file "{edit_args.filename}": {str(e)}', success=False)
        except Exception as e:
            return ContinueResult(f'Unexpected error editing file "{edit_args.filename}": {str(e)}', success=False)

    def _parse_line_range(self, token: str) -> tuple[tuple[int, int], None] | tuple[None, str]:
        try:
            if '-' in token:
                start_line, end_line = map(int, token.split('-'))
            else:
                start_line = end_line = int(token)
            return (start_line, end_line), None
        except ValueError:
            return None, 'Invalid line range format. Use format "start-end" (e.g., "1-5")'

    def _parse_content(self, mode_class, edit_mode: str, parts: list, body: str) -> tuple[str | None, None] | tuple[None, str]:
        if mode_class.allows_content:
            if len(parts) > 3:
                return None, f'For {edit_mode} mode, content must start on the following line, not on the same line'
            content = body
            if content.endswith('\n') and not content.endswith('\n\n'):
                content = content[:-1]
            return content, None
        else:
            if len(parts) > 3:
                return None, f'{edit_mode.capitalize()} mode does not accept content arguments'
            return None, None

    def parse_arguments(self, raw_call):
        args = raw_call.arguments
        body = raw_call.body

        if not args:
            return None, 'No arguments specified'

        try:
            parts = split_arguments(args.strip())
        except ValueError as e:
            return None, f"Error parsing arguments: {str(e)}"

        if len(parts) < 2:
            return None, 'Usage: edit-file <filename> <edit_mode> <line_range>'

        filename, edit_mode = parts[:2]

        mode_class = self.modes.get(edit_mode)
        if mode_class is None:
            valid_modes = ", ".join(self.modes.keys())
            return None, f'Invalid edit mode: {edit_mode}. Supported modes: {valid_modes}'

        # All modes require line_range
        if len(parts) < 3:
            return None, 'Usage: edit-file <filename> <edit_mode> <line_range>'

        line_range_token = parts[2]
        line_range, error = self._parse_line_range(line_range_token)
        if error:
            return None, error
        start_line, end_line = line_range

        new_content, error = self._parse_content(mode_class, edit_mode, parts, body)
        if error:
            return None, error

        return EditFileArgs(
            filename=filename,
            edit_mode=edit_mode,
            start_line=start_line,
            end_line=end_line,
            new_content=new_content
        ), None

    @staticmethod
    def _format_diff(diff_lines):
        formatted_lines = []
        for line in diff_lines:
            if line.endswith("\n"):
                formatted_lines.append(line.rstrip("\n"))
            else:
                formatted_lines.append(line)
                if line and line[0] in (" ", "-", "+"):
                    formatted_lines.append("\\ No newline at end of file")
        return "\n".join(formatted_lines)
