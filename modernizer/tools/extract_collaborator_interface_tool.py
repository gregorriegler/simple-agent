from .base_tool import BaseTool

class ExtractCollaboratorInterfaceTool(BaseTool):
    name = 'extract-collaborator-interface'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    @property
    def description(self):
        return self.get_description_from_csharp('extract-collaborator-interface')
        
    def execute(self, args):
        arg_list = args.split()
        return self.runcommand('dotnet', ['run', '--project', 'refactoring-tools/RoslynRefactoring/RoslynRefactoring.csproj', '--', 'extract-collaborator-interface'] + arg_list)