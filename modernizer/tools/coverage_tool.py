from .base_tool import BaseTool

class CoverageTool(BaseTool):
    name = 'coverage'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, path):
        return self.runcommand('dotnet', ['test', path, '--collect:"XPlat Code Coverage"'])