from ..application.tool_library import ContinueResult, ToolResult
from .base_tool import BaseTool, ToolArgument
from .argument_parser import split_arguments
import os
import re
from dataclasses import dataclass


@dataclass
class PatchFileArgs:
    filename: str
    patch_content: str


class PatchFileTool(BaseTool):
    name = "patch-file"
    description = "Apply a unified diff patch to a file"
    arguments = [
        ToolArgument(
            name="filename",
            type="string",
            required=True,
            description="Path to the file to patch",
        ),
        ToolArgument(
            name="patch_content",
            type="string",
            required=True,
            description="Unified diff patch content to apply",
        ),
    ]
    examples = [
        {
            "filename": "myfile.txt",
            "patch_content": "@@ -1,3 +1,3 @@\\n-old line\\n+new line\\n context line",
        },
        {
            "filename": "test.py",
            "patch_content": "@@ -5,2 +5,2 @@\\n-    old_var = 1\\n+    new_var = 2",
        },
    ]

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    @staticmethod
    def _parse_arguments(args):
        if not args:
            return None, 'No arguments specified'

        try:
            parts = split_arguments(args)
        except ValueError as e:
            return None, f"Error parsing arguments: {str(e)}"

        if len(parts) < 2:
            return None, 'Usage: patch-file <filename> <patch_content>'

        filename = parts[0]

        # Find the position after the filename to get the patch content
        pos = args.find(filename) + len(filename)
        while pos < len(args) and args[pos] == ' ':
            pos += 1

        if pos >= len(args):
            return None, 'Patch content is required'

        patch_content = args[pos:]

        # Handle quoted patch content
        if patch_content.startswith('"') and patch_content.endswith('"'):
            patch_content = patch_content[1:-1]
            patch_content = patch_content.replace('\\n', '\n')

        patch_args = PatchFileArgs(
            filename=filename,
            patch_content=patch_content
        )
        return patch_args, None

    @staticmethod
    def _parse_patch_header(header_line):
        """Parse a patch header line like '@@ -1,3 +1,3 @@'"""
        match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', header_line.strip())
        if not match:
            return None

        old_start = int(match.group(1))
        old_count = int(match.group(2)) if match.group(2) else 1
        new_start = int(match.group(3))
        new_count = int(match.group(4)) if match.group(4) else 1

        return {
            'old_start': old_start,
            'old_count': old_count,
            'new_start': new_start,
            'new_count': new_count
        }

    @staticmethod
    def _apply_patch_hunk(lines, hunk_info, hunk_lines):
        """Apply a single patch hunk to the file lines"""
        old_start = hunk_info['old_start']
        old_count = hunk_info['old_count']

        # Convert to 0-based indexing
        start_idx = old_start - 1

        new_lines = []
        old_line_idx = start_idx
        hunk_idx = 0

        # Add lines before the patch
        new_lines.extend(lines[:start_idx])

        # Process the hunk
        while hunk_idx < len(hunk_lines):
            line = hunk_lines[hunk_idx]

            if line.startswith(' '):
                # Context line - should match
                context_line = line[1:]
                if old_line_idx < len(lines):
                    if lines[old_line_idx].rstrip('\n') != context_line.rstrip('\n'):
                        return None, f"Context mismatch at line {old_line_idx + 1}"

                    # Check if we need to add a newline to the context line
                    # This happens when the context line doesn't end with newline but we're adding lines after it
                    context_line_to_add = lines[old_line_idx]

                    # Look ahead to see if there are any additions coming after this context line
                    has_additions_after = False
                    for j in range(hunk_idx + 1, len(hunk_lines)):
                        if hunk_lines[j].startswith('+'):
                            has_additions_after = True
                            break
                        elif hunk_lines[j].startswith('-') or hunk_lines[j].startswith(' '):
                            break

                    # If context line doesn't end with newline but we have additions after, add newline
                    if (has_additions_after and
                        not context_line_to_add.endswith('\n')):
                        context_line_to_add += '\n'

                    new_lines.append(context_line_to_add)
                    old_line_idx += 1
                else:
                    return None, f"Context line beyond file end at line {old_line_idx + 1}"
            elif line.startswith('-'):
                # Deletion - should match and skip
                deleted_line = line[1:]
                if old_line_idx < len(lines):
                    if lines[old_line_idx].rstrip('\n') != deleted_line.rstrip('\n'):
                        return None, f"Deletion mismatch at line {old_line_idx + 1}"
                    old_line_idx += 1
                else:
                    return None, f"Deletion line beyond file end at line {old_line_idx + 1}"
            elif line.startswith('+'):
                # Addition - add new line
                added_line = line[1:]
                # Always ensure added lines have proper newlines
                # Check if we need to add a newline
                needs_newline = True

                # If this is the very last line being added and the original file
                # doesn't end with a newline, then don't add one
                if (hunk_idx == len(hunk_lines) - 1 and  # This is the last line in the hunk
                    old_line_idx >= len(lines) and       # We're at or past EOF
                    len(lines) > 0 and                   # File is not empty
                    not lines[-1].endswith('\n')):       # Original file doesn't end with newline
                    needs_newline = False

                if needs_newline and not added_line.endswith('\n'):
                    added_line += '\n'

                new_lines.append(added_line)

            hunk_idx += 1

        # Add remaining lines after the patch
        new_lines.extend(lines[old_line_idx:])

        return new_lines, None

    def execute(self, args) -> ToolResult:
        patch_args, error = self._parse_arguments(args)
        if error:
            return ContinueResult(error, success=False)

        return self._apply_patch(patch_args)

    def _apply_patch(self, patch_args):
        try:
            if not os.path.exists(patch_args.filename):
                return ContinueResult(f'File "{patch_args.filename}" not found', success=False)

            with open(patch_args.filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Parse the patch content
            patch_lines = patch_args.patch_content.splitlines()

            if not patch_lines:
                return ContinueResult("Empty patch content", success=False)

            # Find the hunk header
            hunk_header = None
            hunk_start_idx = 0

            for i, line in enumerate(patch_lines):
                if line.startswith('@@'):
                    hunk_header = line
                    hunk_start_idx = i + 1
                    break

            if not hunk_header:
                return ContinueResult("No valid patch hunk found (missing @@ header)", success=False)

            # Parse the hunk header
            hunk_info = self._parse_patch_header(hunk_header)
            if not hunk_info:
                return ContinueResult("Invalid patch hunk header format", success=False)

            # Extract hunk lines
            hunk_lines = patch_lines[hunk_start_idx:]

            # Apply the patch
            new_lines, error = self._apply_patch_hunk(lines, hunk_info, hunk_lines)
            if error:
                return ContinueResult(f"Patch application failed: {error}", success=False)

            if new_lines is None:
                return ContinueResult("Patch application failed: no result lines", success=False)

            # Write back to file
            with open(patch_args.filename, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            return ContinueResult(f"Successfully applied patch to {patch_args.filename}")

        except OSError as e:
            return ContinueResult(f'Error patching file "{patch_args.filename}": {str(e)}', success=False)
        except Exception as e:
            return ContinueResult(f'Unexpected error patching file "{patch_args.filename}": {str(e)}', success=False)
