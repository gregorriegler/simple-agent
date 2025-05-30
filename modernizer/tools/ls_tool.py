from .base_tool import BaseTool

class LsTool(BaseTool):
    name = 'ls'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        
    def execute(self, path='.'):
        return self.runcommand('ls', ['-la', path] if path else ['-la'])
