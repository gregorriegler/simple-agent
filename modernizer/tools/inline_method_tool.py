from .base_tool import BaseTool

class InlineMethodTool(BaseTool):
    name = 'inline-method'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, args):
        arg_list = args.split()
        return self.runcommand('dotnet', ['run', '--project', 'refactoring-tools/RoslynRefactoring/RoslynRefactoring.csproj', '--', 'inline-method'] + arg_list)
