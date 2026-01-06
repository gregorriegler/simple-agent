from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult, ToolResultStatus
from .argument_parser import split_arguments
from .base_tool import BaseTool


class CatTool(BaseTool):
    name = "cat"
    description = "Display file contents with line numbers"
    arguments = ToolArguments(
        header=[
            ToolArgument(
                name="filename",
                type="string",
                required=True,
                description="Path to the file to display",
            ),
            ToolArgument(
                name="line_range",
                type="string",
                required=False,
                description="Optional line range in format 'start-end' (e.g., '1-10')",
            ),
            ToolArgument(
                name="with_line_numbers",
                type="string",
                required=False,
                description="Optional parameter to show line numbers, e.g. 'with_line_numbers'",
            ),
        ]
    )
    examples = [
        {
            "reasoning": "I want to display a file to see its contents.",
            "filename": "myfile.txt",
            "result": "     1\tLine 1 of file\n     2\tLine 2 of file",
        },
        {"filename": "script.py", "line_range": "1-20"},
        {"filename": "script.py", "with_line_numbers": "with_line_numbers"},
    ]

    def _parse_arguments(self, args):
        if not args:
            return None, None, False, "STDERR: cat: missing file operand"

        try:
            parts = split_arguments(args)
        except ValueError as exc:
            return None, None, False, f"STDERR: cat: {exc}"

        if not parts:
            return None, None, False, "STDERR: cat: missing file operand"

        filename = parts[0]
        line_range = None
        with_line_numbers = False

        for part in parts[1:]:
            if part == "with_line_numbers":
                with_line_numbers = True
            elif "-" in part:
                line_range = part
            else:
                return None, None, False, f"STDERR: cat: invalid argument '{part}'"

        return filename, line_range, with_line_numbers, None

    def _validate_range(self, line_range):
        try:
            start_line, end_line = map(int, line_range.split("-"))
        except ValueError:
            return (
                None,
                None,
                f"STDERR: Invalid range format '{line_range}'. Use format 'start-end' (e.g., '1-5')",
            )

        if start_line > end_line:
            return (
                None,
                None,
                f"STDERR: Start line ({start_line}) cannot be greater than end line ({end_line})",
            )

        return start_line, end_line, None

    async def execute(self, raw_call):
        args = raw_call.arguments
        filename, line_range, with_line_numbers, error = self._parse_arguments(args)
        if error:
            return SingleToolResult(error, status=ToolResultStatus.FAILURE)

        if line_range:
            start_line, end_line, error = self._validate_range(line_range)
            if error:
                return SingleToolResult(error, status=ToolResultStatus.FAILURE)
            output, success = self._read_file_range(
                filename, start_line, end_line, with_line_numbers
            )
            status = ToolResultStatus.SUCCESS if success else ToolResultStatus.FAILURE
            return SingleToolResult(output, status=status)
        elif with_line_numbers:
            result = await self.run_command_async("cat", ["-n", filename])
            status = (
                ToolResultStatus.SUCCESS
                if result["success"]
                else ToolResultStatus.FAILURE
            )
            return SingleToolResult(result["output"], status=status)
        else:
            result = await self.run_command_async("cat", [filename])
            status = (
                ToolResultStatus.SUCCESS
                if result["success"]
                else ToolResultStatus.FAILURE
            )
            return SingleToolResult(result["output"], status=status)

    def _read_file_range(self, filename, start_line, end_line, with_line_numbers):
        try:
            with open(filename, encoding="utf-8") as f:
                lines = f.readlines()

            if not lines:
                return "", True

            start_idx = start_line - 1
            end_idx = min(end_line, len(lines))

            if start_idx >= len(lines):
                return "", True

            return self._format_output(
                lines, start_idx, end_idx, with_line_numbers
            ), True

        except FileNotFoundError:
            return f"STDERR: cat: '{filename}': No such file or directory", False
        except Exception as e:
            return f"STDERR: cat: '{filename}': {str(e)}", False

    def _format_output(self, lines, start_idx, end_idx, with_line_numbers):
        result_lines = []
        for i in range(start_idx, end_idx):
            line = lines[i]
            if with_line_numbers:
                result_lines.append(f"{i + 1:6}\t{line}")
            else:
                result_lines.append(line)

        return "".join(result_lines).rstrip("\n")
