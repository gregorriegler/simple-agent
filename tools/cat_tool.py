from .base_tool import BaseTool

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
        "/cat myfile.txt",
        "/cat script.py 1-20"
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def _parse_arguments(self, args):
        """Parse command arguments into filename and optional line range."""
        if not args:
            return None, None, {'output': 'STDERR: cat: missing file operand'}

        # Parse arguments - split by space to separate filename and optional range
        parts = args.split()
        filename = parts[0]
        line_range = parts[1] if len(parts) > 1 else None

        return filename, line_range, None

    def _validate_range(self, line_range):
        """Validate and parse line range string into start and end line numbers."""
        # Parse line range (e.g., "1-5")
        try:
            start_line, end_line = map(int, line_range.split('-'))
        except ValueError:
            return None, None, {'output': f"STDERR: Invalid range format '{line_range}'. Use format 'start-end' (e.g., '1-5')"}

        if start_line > end_line:
            return None, None, {'output': f"STDERR: Start line ({start_line}) cannot be greater than end line ({end_line})"}

        return start_line, end_line, None

    def execute(self, args):
        filename, line_range, error = self._parse_arguments(args)
        if error:
            return error

        if line_range is None:
            return self.runcommand('cat', ['-n', filename])

        start_line, end_line, error = self._validate_range(line_range)
        if error:
            return error

        return self._read_file_range(filename, start_line, end_line)

    def _read_file_range(self, filename, start_line, end_line):
        """Read file and extract specified line range with formatting."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Handle empty file or range beyond file length
            if not lines:
                return {'output': ""}  # Empty file, no output

            # Convert to 0-based indexing and extract range
            start_idx = start_line - 1
            end_idx = min(end_line, len(lines))

            if start_idx >= len(lines):
                return {'output': ""}  # Range beyond file length, no output

            return self._format_output(lines, start_idx, end_idx)

        except FileNotFoundError:
            return {'output': f"STDERR: cat: '{filename}': No such file or directory"}
        except Exception as e:
            return {'output': f"STDERR: cat: '{filename}': {str(e)}"}

    def _format_output(self, lines, start_idx, end_idx):
        """Format output lines with line numbers."""
        result_lines = []
        for i in range(start_idx, end_idx):
            result_lines.append(f"{i + 1:6}\t{lines[i]}")

        output = "".join(result_lines).rstrip('\n')
        return {'output': output}
