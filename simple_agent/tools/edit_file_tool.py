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

    @staticmethod
    def _parse_arguments(args):
        if not args:
            return None, 'No arguments specified'

        original_args = args
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

        # If there are more parts, reconstruct the content from the remaining parts
        if len(parts) > 3:
            # Find the position in the original string after the third token
            # to preserve the original spacing
            pos = 0
            for i, token in enumerate([filename, edit_mode, line_range_token]):
                token_pos = args.find(token, pos)
                if token_pos == -1:
                    break
                pos = token_pos + len(token)

            # Skip only one space after the third token (standard separator)
            if pos < len(args) and args[pos] == ' ':
                pos += 1

            new_content = args[pos:] if pos < len(args) else None
        else:
            new_content = None

        if new_content == '':
            new_content = None

        if new_content and new_content.startswith('"') and new_content.endswith('"'):
            new_content = new_content[1:-1]
            new_content = new_content.replace('\\n', '\n')

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

    @staticmethod
    def _normalize_line_range(start_line, end_line, total_lines):
        if total_lines == 0:
            return None

        if end_line < 1 or start_line > total_lines:
            return None

        normalized_start = max(1, start_line)
        normalized_end = min(total_lines, end_line)

        if normalized_start > normalized_end:
            return None

        return normalized_start, normalized_end

    @staticmethod
    def _detect_indentation(lines, line_number):
        if not lines or line_number < 1 or line_number > len(lines):
            return ""

        line = lines[line_number - 1]
        indent = ""
        for char in line:
            if char in [' ', '\t']:
                indent += char
            else:
                break
        return indent

    @staticmethod
    def _apply_indentation(content, indent, raw_mode):
        if raw_mode or not content:
            return content

        # If content already starts with whitespace, preserve it as-is
        if content.startswith(' ') or content.startswith('\t'):
            return content

        # Only apply indentation if there's indentation to apply
        if not indent:
            return content

        lines = content.splitlines(keepends=True)
        if lines:
            lines[0] = indent + lines[0]

        return ''.join(lines)

    def execute(self, args):
        edit_args, error = self._parse_arguments(args)
        if error:
            return ContinueResult(error)

        return self._perform_file_edit(edit_args)

    def _perform_file_edit(self, edit_args):
        try:
            if not os.path.exists(edit_args.filename):
                return ContinueResult(f'File "{edit_args.filename}" not found')

            with open(edit_args.filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            normalized_range = self._normalize_line_range(edit_args.start_line, edit_args.end_line, len(lines))

            if edit_args.edit_mode == "insert":
                inserting_between_lines = edit_args.start_line <= len(lines)

                content_to_insert = edit_args.new_content
                if content_to_insert is not None and not edit_args.raw:
                    if edit_args.start_line <= len(lines):
                        indent = self._detect_indentation(lines, edit_args.start_line)
                        content_to_insert = self._apply_indentation(content_to_insert, indent, edit_args.raw)

                if content_to_insert is None:
                    new_content = ['\n']
                elif not content_to_insert.endswith('\n') and inserting_between_lines:
                    content_with_newline = content_to_insert + '\n'
                    new_content = content_with_newline.splitlines(keepends=True)
                else:
                    new_content = content_to_insert.splitlines(keepends=True)

                if edit_args.start_line > len(lines):
                    # Ensure last line has newline if it exists
                    if lines and not lines[-1].endswith('\n'):
                        lines[-1] = lines[-1] + '\n'

                    # Pad with empty lines if inserting far beyond the end
                    lines_to_add = edit_args.start_line - len(lines) - 1
                    if lines_to_add > 0:
                        lines.extend(['\n'] * lines_to_add)

                    lines.extend(new_content)
                else:
                    lines[edit_args.start_line - 1:edit_args.start_line - 1] = new_content
                new_lines = lines
            elif edit_args.edit_mode == "delete":
                if normalized_range is None:
                    new_lines = lines
                else:
                    start_line, end_line = normalized_range
                    new_lines = self._delete_lines(lines, start_line, end_line)
                    if self._range_reaches_file_end(normalized_range, len(lines)):
                        new_lines = self._trim_terminal_newline(lines, new_lines)
            elif edit_args.edit_mode == "replace":
                if len(lines) == 0 and edit_args.start_line == 0 and edit_args.end_line == 0:
                    if edit_args.new_content is None:
                        new_lines = []
                    elif '\n' in edit_args.new_content:
                        new_lines = [line + '\n' for line in edit_args.new_content.split('\n') if line]
                    else:
                        new_lines = [edit_args.new_content + '\n']
                else:
                    if normalized_range is None:
                        new_lines = lines
                    else:
                        start_line, end_line = normalized_range

                        content_to_replace = edit_args.new_content
                        if content_to_replace is not None and not edit_args.raw:
                            indent = self._detect_indentation(lines, start_line)
                            content_to_replace = self._apply_indentation(content_to_replace, indent, edit_args.raw)

                        new_lines = self._replace_lines(lines, start_line, end_line, content_to_replace)
                        if content_to_replace is None:
                            if self._range_reaches_file_end(normalized_range, len(lines)):
                                new_lines = self._trim_terminal_newline(lines, new_lines)
            else:
                return ContinueResult(
                    f"Invalid edit mode: {edit_args.edit_mode}. Supported modes: insert, delete, replace")

            # Write back to file
            with open(edit_args.filename, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            return ContinueResult(f"Successfully edited {edit_args.filename}")

        except OSError as e:
            return ContinueResult(f'Error editing file "{edit_args.filename}": {str(e)}')
        except Exception as e:
            return ContinueResult(f'Unexpected error editing file "{edit_args.filename}": {str(e)}')

    @staticmethod
    def _delete_lines(lines, start_line, end_line):
        lines_to_delete = set(range(start_line, end_line + 1))
        return [line for i, line in enumerate(lines, start=1) if i not in lines_to_delete]

    @staticmethod
    def _replace_lines(lines, start_line, end_line, new_content):
        start_idx = start_line - 1
        end_idx = end_line - 1

        if new_content is None:
            replacement_lines = []
        elif '\n' in new_content:
            replacement_lines = [line + '\n' for line in new_content.split('\n') if line]
        else:
            last_replaced_line = lines[end_idx]
            if last_replaced_line.endswith('\n'):
                replacement_lines = [new_content + '\n']
            else:
                replacement_lines = [new_content]

        return lines[:start_idx] + replacement_lines + lines[end_idx + 1:]

    @staticmethod
    def _range_reaches_file_end(normalized_range, total_lines):
        if normalized_range is None:
            return False
        _, normalized_end = normalized_range
        return normalized_end == total_lines

    @staticmethod
    def _trim_terminal_newline(original_lines, new_lines):
        if not original_lines or not new_lines:
            return new_lines
        if original_lines[-1].endswith('\n'):
            return new_lines
        if not new_lines[-1].endswith('\n'):
            return new_lines
        adjusted_lines = new_lines[:]
        adjusted_lines[-1] = adjusted_lines[-1][:-1]
        return adjusted_lines
