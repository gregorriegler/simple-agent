import difflib
import os
from dataclasses import dataclass

from .argument_parser import split_arguments
from .base_tool import BaseTool
from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult


@dataclass
class ReplaceFileArgs:
    filename: str
    old_string: str
    new_string: str
    replace_mode: str


class FileReplacer:
    """Handles file content replacement operations."""

    def __init__(self, filename):
        self.filename = filename
        self.original_content = ""
        self.new_content = ""

    def load_file(self):
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f'File "{self.filename}" not found')

        with open(self.filename, 'r', encoding='utf-8') as f:
            self.original_content = f.read()

    def save_file(self):
        with open(self.filename, 'w', encoding='utf-8', newline="\n") as f:
            f.write(self.new_content)

    def replace(self, old_string: str, new_string: str, replace_mode: str):
        """Replace content using exact string matching."""
        content = self.original_content

        # Count occurrences for uniqueness check
        count = content.count(old_string)
        if count == 0:
            raise ValueError(
                "String not found in file. Make sure the old_string matches exactly (including whitespace).")

        if replace_mode == "single":
            self.new_content = content.replace(old_string, new_string, 1)
        elif replace_mode == "all":
            self.new_content = content.replace(old_string, new_string)
        elif replace_mode.startswith("nth:"):
            try:
                n = int(replace_mode.split(":")[1])
                if n <= 0:
                    raise ValueError("Nth occurrence must be a positive integer.")

                start_index = -1
                for i in range(n):
                    start_index = content.find(old_string, start_index + 1)
                    if start_index == -1:
                        raise ValueError(f"Could not find the {n}th occurrence of the string.")

                self.new_content = content[:start_index] + new_string + content[start_index + len(old_string):]
            except (ValueError, IndexError):
                raise ValueError("Invalid format for nth. Expected 'nth:positive_integer'.")
        else:
            raise ValueError(f"Invalid replace_mode: {replace_mode}")

    def build_diff(self):
        """Build a unified diff between original and new content."""
        original_lines = self.original_content.splitlines(keepends=True)
        new_lines = self.new_content.splitlines(keepends=True)

        diff_lines = list(
            difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=f"{self.filename} (original)",
                tofile=f"{self.filename} (updated)",
            )
        )
        return diff_lines


class ReplaceFileContentTool(BaseTool):
    name = "replace-file-content"
    description = "Replace exact string matches in files. Unlike edit-file, this tool uses string matching instead of line numbers, making it more reliable for replacing specific content."

    arguments = ToolArguments(header=[
        ToolArgument(
            name="filename",
            type="string",
            required=True,
            description="Path to the file to edit",
        ),
        ToolArgument(
            name="replace_mode",
            type="string",
            required=True,
            description="Replace mode: 'single', 'all'. 'single' replaces only the first occurence. 'all' replaces all occurences.",
        ),
    ], body=ToolArgument(
        name="content",
        type="string",
        required=True,
        description="Content with @@@ separator: text before @@@ is search string, text after is replacement string",
    ))

    examples = [
        {
            "reasoning": "I'll replace the first occurrence of text in a file.",
            "filename": "test.txt",
            "replace_mode": "single",
            "content": "search content\n@@@\nreplacement content",
            "result": "Successfully replaced content in test.txt"
        },
        "🛠️[replace-file-content test.txt all]\nfoo\n@@@\nbar\n🛠️[/end]",
        "🛠️[replace-file-content test.txt nth:2]\nold_value = 1\n@@@\nnew_value = 2\n🛠️[/end]",
    ]

    async def execute(self, raw_call):
        replace_args, error = self.parse_arguments(raw_call)
        if error or replace_args is None:
            return SingleToolResult(error or "Failed to parse arguments", success=False)

        try:
            replacer = FileReplacer(replace_args.filename)
            replacer.load_file()

            replacer.replace(
                replace_args.old_string,
                replace_args.new_string,
                replace_args.replace_mode
            )

            diff_lines = replacer.build_diff()

            replacer.save_file()

            if diff_lines:
                diff_message = self._format_diff(diff_lines)
                summary = f"Successfully replaced content in {replace_args.filename}"
                message = f"{summary}\n\n{diff_message}"
                return SingleToolResult(
                    message,
                    display_body=diff_message,
                    display_language="diff",
                )

            summary = f"No changes made to {replace_args.filename}"
            return SingleToolResult(
                summary,
                display_body=summary,
            )

        except FileNotFoundError as e:
            return SingleToolResult(str(e), success=False)
        except ValueError as e:
            return SingleToolResult(str(e), success=False)
        except OSError as e:
            return SingleToolResult(f'Error replacing content in "{replace_args.filename}": {str(e)}', success=False)
        except Exception as e:
            return SingleToolResult(f'Unexpected error replacing content in "{replace_args.filename}": {str(e)}', success=False)

    def _parse_replace_body(self, body: str) -> tuple[tuple[str, str], None] | tuple[None, str]:
        """Parse body with @@@ separator (text before @@@ is search string, text after is replacement)."""
        if not body:
            return None, "replace-file-content requires body with @@@ separator"

        # Find the @@@ separator
        if "@@@" not in body:
            return None, "Missing '@@@' separator between search and replacement content"

        # Split on @@@ separator
        parts = body.split("@@@", 1)
        if len(parts) != 2:
            return None, "Body must contain exactly one '@@@' separator"

        old_string = parts[0].rstrip('\n')
        new_string = parts[1].lstrip('\n')

        return (old_string, new_string), None

    def parse_arguments(self, raw_call):
        args = raw_call.arguments
        body = raw_call.body

        if not args:
            return None, 'No arguments specified'

        try:
            parts = split_arguments(args.strip())
        except ValueError as e:
            return None, f"Error parsing arguments: {str(e)}"

        if len(parts) < 1:
            return None, 'Usage: replace-file-content <filename> [replace_mode]'

        filename = parts[0]
        replace_mode = "single"

        if len(parts) > 1:
            replace_mode = parts[1]

        if len(parts) > 2:
            return None, "Too many arguments for replace-file-content"

        if replace_mode not in ["single", "all"] and not replace_mode.startswith("nth:"):
            return None, f"Invalid replace_mode: {replace_mode}"

        parsed, error = self._parse_replace_body(body)
        if error:
            return None, error
        old_string, new_string = parsed

        return ReplaceFileArgs(
            filename=filename,
            old_string=old_string,
            new_string=new_string,
            replace_mode=replace_mode
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
