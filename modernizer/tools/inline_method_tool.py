from .base_tool import BaseTool

class InlineMethodTool(BaseTool):
    name = 'inline-method'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        self.cwd = 'refactoring-tools/RoslynRefactoring'
        
    def execute(self, args):
        arg_list = args.split()
        return self.runcommand('dotnet', ['run', '--', 'inline-method'] + arg_list, cwd=self.cwd)
