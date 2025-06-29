import os
from .base_tool import BaseTool

class RevertTool(BaseTool):
    name = 'revert'
    description = "Revert changes in a directory to previous state"
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        self.script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'revert.sh')
        
    def execute(self, directory='.'):
        return self.runcommand('bash', [self.script_path, directory])
