from simple_agent.application.tool_result import ContinueResult
from .base_tool import BaseTool
from .argument_parser import create_lexer, split_arguments
import os
from dataclasses import dataclass


@dataclass
class EditFileArgs:
    filename: str
    edit_mode: str
    start_line: int
    end_line: int
    new_content: str | None
    raw: bool = False


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

    def apply_indentation(self, content, line_number, raw_mode):
        if raw_mode or not content:
            return content

        if content.startswith(' ') or content.startswith('\t'):
            return content

        indent = self.get_indentation(line_number)
        if not indent:
            return content

        lines = content.splitlines(keepends=True)
        if lines:
            lines[0] = indent + lines[0]

        return ''.join(lines)

    def normalize_range(self, start_line, end_line):
        total_lines = len(self.lines)
        if total_lines == 0 or end_line < 1 or start_line > total_lines:
            return None

        normalized_start = max(1, start_line)
        normalized_end = min(total_lines, end_line)

        if normalized_start > normalized_end:
            return None

        return normalized_start, normalized_end

    def insert(self, args: EditFileArgs):
        content = self.apply_indentation(args.new_content, args.start_line, args.raw) if args.new_content else None

        if content is None:
            new_content = ['\n']
        else:
            inserting_between_lines = args.start_line <= len(self.lines)
            if not content.endswith('\n') and inserting_between_lines:
                content += '\n'
            new_content = content.splitlines(keepends=True)

        if args.start_line > len(self.lines):
            if self.lines and not self.lines[-1].endswith('\n'):
                self.lines[-1] += '\n'

            lines_to_add = args.start_line - len(self.lines) - 1
            if lines_to_add > 0:
                self.lines.extend(['\n'] * lines_to_add)

            self.lines.extend(new_content)
        else:
            insert_pos = args.start_line - 1
            self.lines[insert_pos:insert_pos] = new_content

    def delete(self, args: EditFileArgs):
        normalized_range = self.normalize_range(args.start_line, args.end_line)
        if normalized_range is None:
            return

        start_line, end_line = normalized_range
        lines_to_delete = set(range(start_line, end_line + 1))
        new_lines = [line for i, line in enumerate(self.lines, start=1)
                    if i not in lines_to_delete]

        # Handle terminal newline trimming when range reaches file end
        if end_line == len(self.lines):
            new_lines = self._trim_terminal_newline(new_lines)

        self.lines = new_lines

    def replace(self, args: EditFileArgs):
        if len(self.lines) == 0 and args.start_line == 0 and args.end_line == 0:
            if args.new_content is None:
                self.lines = []
            elif '\n' in args.new_content:
                self.lines = [line + '\n' for line in args.new_content.split('\n') if line]
            else:
                self.lines = [args.new_content + '\n']
            return

        normalized_range = self.normalize_range(args.start_line, args.end_line)
        if normalized_range is None:
            return

        start_line, end_line = normalized_range
        content = self.apply_indentation(args.new_content, start_line, args.raw) if args.new_content else None

        start_idx = start_line - 1
        end_idx = end_line - 1

        if content is None:
            replacement_lines = []
        elif '\n' in content:
            replacement_lines = [line + '\n' for line in content.split('\n') if line]
        else:
            last_replaced_line = self.lines[end_idx]
            if last_replaced_line.endswith('\n'):
                replacement_lines = [content + '\n']
            else:
                replacement_lines = [content]

        self.lines = (self.lines[:start_idx] +
                     replacement_lines +
                     self.lines[end_idx + 1:])

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


class EditFileTool(BaseTool):
    name = "edit-file"
    description = "Edit files by replacing content in specified line ranges with auto-indent preservation"
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
            "description": "New content to replace or insert at the specified lines. "
                           "By default, indentation is auto-preserved from the target line. "
                           "Use --raw flag to disable auto-indentation. "
                           "Newline behavior: "
                           "With quotes, use \\n for newlines. Without quotes, actual line breaks create newlines. "
                           "If you don't end with a newline and are inserting between lines, one will be added automatically."
        },
        {
            "name": "--raw",
            "type": "flag",
            "required": False,
            "description": "Disable auto-indentation preservation"
        }
    ]
    examples = [
        "🛠️ edit-file myfile.txt replace 1-3 \"Hello World\"",
        "to delete the first line\n🛠️ edit-file test.txt delete 1",
        "to insert a new line at the top\n🛠️ edit-file test.txt insert 1 New Headline",
        "to insert with auto-indent\n🛠️ edit-file test.py insert 3 print('hello')",
        "to insert without auto-indent\n🛠️ edit-file test.py insert 3 --raw print('hello')",
        "to replace with auto-indent\n🛠️ edit-file test.py replace 5 new = 2",
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def parse_arguments(self, args):
        if not args:
            return None, 'No arguments specified'

        raw_mode = '--raw' in args
        if raw_mode:
            args = args.replace('--raw', '').strip()

        try:
            parts = split_arguments(args)
        except ValueError as e:
            return None, f"Error parsing arguments: {str(e)}"

        if len(parts) < 3:
            return None, 'Usage: edit-file <filename> <edit_mode> <line_range> [--raw] [new_content]'

        filename, edit_mode, line_range_token = parts[:3]

        if len(parts) > 3:
            pos = 0
            for token in [filename, edit_mode, line_range_token]:
                token_pos = args.find(token, pos)
                if token_pos == -1:
                    break
                pos = token_pos + len(token)

            if pos < len(args) and args[pos] == ' ':
                pos += 1

            new_content = args[pos:] if pos < len(args) else None
        else:
            new_content = None

        if new_content == '':
            new_content = None

        if new_content and new_content.startswith('"') and new_content.endswith('"'):
            new_content = new_content[1:-1].replace('\\n', '\n')

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
            new_content=new_content,
            raw=raw_mode
        )
        return edit_args, None

    def execute(self, args):
        edit_args, error = self.parse_arguments(args)
        if error or edit_args is None:
            return ContinueResult(error or "Failed to parse arguments")

        try:
            editor = FileEditor(edit_args.filename)
            editor.load_file()

            if edit_args.edit_mode == 'insert':
                editor.insert(edit_args)
            elif edit_args.edit_mode == 'delete':
                editor.delete(edit_args)
            elif edit_args.edit_mode == 'replace':
                editor.replace(edit_args)
            else:
                return ContinueResult(
                    f"Invalid edit mode: {edit_args.edit_mode}. Supported modes: insert, delete, replace")

            editor.save_file()
            return ContinueResult(f"Successfully edited {edit_args.filename}")

        except FileNotFoundError as e:
            return ContinueResult(str(e))
        except OSError as e:
            return ContinueResult(f'Error editing file "{edit_args.filename}": {str(e)}')
        except Exception as e:
            return ContinueResult(f'Unexpected error editing file "{edit_args.filename}": {str(e)}')
