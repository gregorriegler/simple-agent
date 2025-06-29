from .base_tool import BaseTool

class CatTool(BaseTool):
    name = 'cat'
    description = "Display file contents with line numbers"
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, filename):
        return self.runcommand('cat', ['-n', filename])
