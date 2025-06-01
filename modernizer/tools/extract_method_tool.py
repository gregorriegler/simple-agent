from .base_tool import BaseTool

class ExtractMethodTool(BaseTool):
    name = 'extract-method'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, args):
        arg_list = args.split()
        return self.runcommand('dotnet', ['run', '--project', 'refactoring-tools/RoslynRefactoring/RoslynRefactoring.csproj', '--', 'extract-method'] + arg_list)
