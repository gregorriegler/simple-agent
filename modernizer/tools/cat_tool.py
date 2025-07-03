from .base_tool import BaseTool

class CatTool(BaseTool):
    name = 'cat'
    description = "Display file contents with line numbers"
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, args):
        if not args:
            return {'success': False, 'output': 'STDERR: cat: missing file operand'}
        
        # Parse arguments - split by space to separate filename and optional range
        parts = args.split()
        filename = parts[0]
        line_range = parts[1] if len(parts) > 1 else None
        
        if line_range is None:
            return self.runcommand('cat', ['-n', filename])
        
        # Parse line range (e.g., "1-5")
        try:
            start_line, end_line = map(int, line_range.split('-'))
        except ValueError:
            return {'success': False, 'output': f"STDERR: Invalid range format '{line_range}'. Use format 'start-end' (e.g., '1-5')"}
        
        if start_line > end_line:
            return {'success': False, 'output': f"STDERR: Start line ({start_line}) cannot be greater than end line ({end_line})"}
        
        # Read file and extract line range
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            # Handle empty file or range beyond file length
            if not lines:
                return {'success': True, 'output': ""}  # Empty file, no output
            
            # Convert to 0-based indexing and extract range
            start_idx = start_line - 1
            end_idx = min(end_line, len(lines))
            
            if start_idx >= len(lines):
                return {'success': True, 'output': ""}  # Range beyond file length, no output
            
            # Format output with line numbers
            result_lines = []
            for i in range(start_idx, end_idx):
                result_lines.append(f"{i + 1:6}\t{lines[i]}")
            
            output = "".join(result_lines).rstrip('\n')
            return {'success': True, 'output': output}
            
        except FileNotFoundError:
            return {'success': False, 'output': f"STDERR: cat: '{filename}': No such file or directory"}
        except Exception as e:
            return {'success': False, 'output': f"STDERR: cat: '{filename}': {str(e)}"}
