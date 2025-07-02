from .base_tool import BaseTool
import os
from dataclasses import dataclass

@dataclass
class EditFileArgs:
    filename: str
    start_line: int
    end_line: int
    new_content: str

class EditFileTool(BaseTool):
    name = "edit-file"
    description = "Edit files by replacing content in specified line ranges"
    
    # Constants for argument parsing
    MAX_SPLIT_PARTS = 3  # Split into filename, start_line, end_line, new_content
    EXPECTED_ARG_COUNT = 4

    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand

    def _parse_arguments(self, args):
        """Parse and validate command arguments."""
        if not args:
            return None, {'success': False, 'output': 'No arguments specified', 'returncode': 1}
        
        parts = args.split(' ', self.MAX_SPLIT_PARTS)
        if len(parts) < self.EXPECTED_ARG_COUNT:
            return None, {'success': False, 'output': 'Usage: edit-file <filename> <start_line> <end_line> <new_content>', 'returncode': 1}
        
        try:
            # Convert literal \n in the new_content to actual newlines
            new_content = parts[3].replace('\\n', '\n')
            edit_args = EditFileArgs(
                filename=parts[0],
                start_line=int(parts[1]),
                end_line=int(parts[2]),
                new_content=new_content
            )
            return edit_args, None
        except ValueError:
            return None, {'success': False, 'output': 'Line numbers must be integers', 'returncode': 1}

    def _validate_line_range(self, start_line, end_line, total_lines):
        """Validate that the line range is valid for the file."""
        if start_line < 1 or end_line < 1 or start_line > total_lines or end_line > total_lines:
            return {'success': False, 'output': f"Invalid line range: {start_line}-{end_line} for file with {total_lines} lines", 'returncode': 1}
        
        if start_line > end_line:
            return {'success': False, 'output': f"Start line ({start_line}) cannot be greater than end line ({end_line})", 'returncode': 1}
        
        return None

    def _perform_file_edit(self, edit_args):
        """Perform the actual file reading, editing, and writing operations."""
        try:
            # Check if file exists
            if not os.path.exists(edit_args.filename):
                return {'success': False, 'output': f'File "{edit_args.filename}" not found', 'returncode': 1}
            
            # Read the file
            with open(edit_args.filename, 'r') as f:
                lines = f.readlines()
            
            # Validate line range
            validation_error = self._validate_line_range(edit_args.start_line, edit_args.end_line, len(lines))
            if validation_error:
                return validation_error
            
            # Replace the specified lines with new content
            # Convert to 0-based indexing
            start_idx = edit_args.start_line - 1
            end_idx = edit_args.end_line - 1
            
            # Replace the lines
            # Handle multi-line content by splitting on \n and ensuring proper line endings
            if '\n' in edit_args.new_content:
                replacement_lines = [line + '\n' for line in edit_args.new_content.split('\n') if line]
            else:
                # For single-line content, preserve the original line ending behavior
                # Check if the last line being replaced had a newline to determine if we should add one
                last_replaced_line = lines[end_idx] if end_idx < len(lines) else ''
                if last_replaced_line.endswith('\n'):
                    replacement_lines = [edit_args.new_content + '\n']
                else:
                    replacement_lines = [edit_args.new_content]
            
            new_lines = lines[:start_idx] + replacement_lines + lines[end_idx + 1:]
            
            # Write back to file
            with open(edit_args.filename, 'w') as f:
                f.writelines(new_lines)
            
            return {'success': True, 'output': f"Successfully edited {edit_args.filename}, lines {edit_args.start_line}-{edit_args.end_line}", 'returncode': 0}
            
        except OSError as e:
            return {'success': False, 'output': f'Error editing file "{edit_args.filename}": {str(e)}', 'returncode': 1}
        except Exception as e:
            return {'success': False, 'output': f'Unexpected error editing file "{edit_args.filename}": {str(e)}', 'returncode': 1}

    def execute(self, args):
        edit_args, error = self._parse_arguments(args)
        if error:
            return error
        
        return self._perform_file_edit(edit_args)