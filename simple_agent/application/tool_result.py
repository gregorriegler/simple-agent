from dataclasses import dataclass

@dataclass
class ToolResult:
    feedback: str

    def __init__(self, feedback=""):
        self.feedback = feedback

    def __str__(self) : return self.feedback

@dataclass
class ContinueResult(ToolResult):
    def __init__(self, feedback=""):
        super().__init__(feedback)

@dataclass
class CompleteResult(ToolResult):
    pass
