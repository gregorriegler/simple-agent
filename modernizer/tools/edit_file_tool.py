from .base_tool import BaseTool
import os

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
        
        filename = parts[0]
        try:
            start_line = int(parts[1])
            end_line = int(parts[2])
            new_content = parts[3]
            return (filename, start_line, end_line, new_content), None
        except ValueError:
            return None, {'success': False, 'output': 'Line numbers must be integers', 'returncode': 1}

    def _validate_line_range(self, start_line, end_line, total_lines):
        """Validate that the line range is valid for the file."""
        if start_line < 1 or end_line < 1 or start_line > total_lines or end_line > total_lines:
            return {'success': False, 'output': f"Invalid line range: {start_line}-{end_line} for file with {total_lines} lines", 'returncode': 1}
        
        if start_line > end_line:
            return {'success': False, 'output': f"Start line ({start_line}) cannot be greater than end line ({end_line})", 'returncode': 1}
        
        return None

    def _perform_file_edit(self, filename, start_line, end_line, new_content):
        """Perform the actual file reading, editing, and writing operations."""
        try:
            # Check if file exists
            if not os.path.exists(filename):
                return {'success': False, 'output': f"File '{filename}' not found", 'returncode': 1}
            
            # Read the file
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            # Validate line range
            validation_error = self._validate_line_range(start_line, end_line, len(lines))
            if validation_error:
                return validation_error
            
            # Replace the specified lines with new content
            # Convert to 0-based indexing
            start_idx = start_line - 1
            end_idx = end_line - 1
            
            # Replace the lines
            new_lines = lines[:start_idx] + [new_content] + lines[end_idx + 1:]
            
            # Write back to file
            with open(filename, 'w') as f:
                f.writelines(new_lines)
            
            return {'success': True, 'output': f"Successfully edited {filename}, lines {start_line}-{end_line}", 'returncode': 0}
            
        except OSError as e:
            return {'success': False, 'output': f"Error editing file '{filename}': {str(e)}", 'returncode': 1}
        except Exception as e:
            return {'success': False, 'output': f"Unexpected error editing file '{filename}': {str(e)}", 'returncode': 1}

    def execute(self, args):
        parsed_args, error = self._parse_arguments(args)
        if error:
            return error
        
        filename, start_line, end_line, new_content = parsed_args
        return self._perform_file_edit(filename, start_line, end_line, new_content)