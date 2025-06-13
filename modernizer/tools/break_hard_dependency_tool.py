from .base_tool import BaseTool

class BreakHardDependencyTool(BaseTool):
    name = 'break-hard-dependency'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, args):
        arg_list = args.split()
        return self.runcommand('dotnet', ['run', '--project', 'refactoring-tools/RoslynRefactoring/RoslynRefactoring.csproj', '--', 'break-hard-dependency'] + arg_list)