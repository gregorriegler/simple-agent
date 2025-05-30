import os
from .base_tool import BaseTool

class TestTool(BaseTool):
    __test__ = False
    name = 'test'
    
    def __init__(self, runcommand):
        super().__init__()
        self.runcommand = runcommand
        self.script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test.sh')
        
    def execute(self, path):
        return self.runcommand('bash', [self.script_path, path])
