from ..application.tool_library import ContinueResult
from .base_tool import BaseTool
from .argument_parser import split_arguments


class CatTool(BaseTool):
    name = 'cat'
    description = "Display file contents with line numbers"
    arguments = [
        {
            "name": "filename",
            "type": "string",
            "required": True,
            "description": "Path to the file to display"
        },
        {
            "name": "line_range",
            "type": "string",
            "required": False,
            "description": "Optional line range in format 'start-end' (e.g., '1-10')"
        }
    ]
    examples = [
        "🛠️ cat myfile.txt",
        "🛠️ cat script.py 1-20"
    ]

    def _parse_arguments(self, args):
        if not args:
            return None, None, 'STDERR: cat: missing file operand'

        try:
            parts = split_arguments(args)
        except ValueError as exc:
            return None, None, f"STDERR: cat: {exc}"

        if not parts:
            return None, None, 'STDERR: cat: missing file operand'

        filename = parts[0]
        line_range = parts[1] if len(parts) > 1 else None

        return filename, line_range, None

    def _validate_range(self, line_range):
        try:
            start_line, end_line = map(int, line_range.split('-'))
        except ValueError:
            return None, None, f"STDERR: Invalid range format '{line_range}'. Use format 'start-end' (e.g., '1-5')"

        if start_line > end_line:
            return None, None, f"STDERR: Start line ({start_line}) cannot be greater than end line ({end_line})"

        return start_line, end_line, None

    def execute(self, args):
        filename, line_range, error = self._parse_arguments(args)
        if error:
            return ContinueResult(error)
        if line_range is None:
            result = self.run_command('cat', ['-n', filename])
            return ContinueResult(result['output'])
        start_line, end_line, error = self._validate_range(line_range)
        if error:
            return ContinueResult(error)
        output = self._read_file_range(filename, start_line, end_line)
        return ContinueResult(output)

    def _read_file_range(self, filename, start_line, end_line):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if not lines:
                return ""

            start_idx = start_line - 1
            end_idx = min(end_line, len(lines))

            if start_idx >= len(lines):
                return ""

            return self._format_output(lines, start_idx, end_idx)

        except FileNotFoundError:
            return f"STDERR: cat: '{filename}': No such file or directory"
        except Exception as e:
            return f"STDERR: cat: '{filename}': {str(e)}"

    def _format_output(self, lines, start_idx, end_idx):
        result_lines = []
        for i in range(start_idx, end_idx):
            result_lines.append(f"{i + 1:6}\t{lines[i]}")

        return "".join(result_lines).rstrip('\n')
