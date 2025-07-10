class BaseTool:
    name = ''
    
    def __init__(self):
        self.runcommand = None
        
    def execute(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement execute()")
