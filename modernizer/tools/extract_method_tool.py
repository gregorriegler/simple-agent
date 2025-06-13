from .base_tool import BaseTool

class ExtractMethodTool(BaseTool):
    name = 'extract-method'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        self._info = None
        
    @property
    def info(self):
        if self._info is None:
            self._info = self.get_info_from_csharp('extract-method')
        return self._info
        
    @property
    def description(self):
        return self.info.get('description', 'Extract selected code into a new method')
    
    @property
    def arguments(self):
        info = self.info
        program_args = info.get('program_arguments', [])
        refactoring_args = info.get('refactoring_arguments', [])
        return {
            'program_arguments': program_args,
            'refactoring_arguments': refactoring_args,
            'all_arguments': program_args + refactoring_args
        }
    
    def get_usage_info(self):
        """Get comprehensive usage information for this tool"""
        info = self.info
        args = self.arguments
        
        usage_info = f"""
Tool: {info.get('name', self.name)}
Description: {info.get('description', 'No description available')}

Usage: {self.name} <project_path> <file_name> <selection> <new_method_name>

Arguments:
  Program Arguments (common to all refactoring tools):
"""
        for arg in args['program_arguments']:
            usage_info += f"    - {arg}\n"
            
        usage_info += "\n  Refactoring-specific Arguments:\n"
        for arg in args['refactoring_arguments']:
            usage_info += f"    - {arg}\n"
            
        return usage_info.strip()
        
    def execute(self, args):
        arg_list = args.split()
        return self.runcommand('dotnet', ['run', '--project', 'refactoring-tools/RoslynRefactoring/RoslynRefactoring.csproj', '--', 'extract-method'] + arg_list)
