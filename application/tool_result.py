from dataclasses import dataclass

@dataclass
class ToolResult:
    feedback: str
    pass
    def __str__(self) : return self.feedback

@dataclass
class ContinueResult(ToolResult):
    pass

@dataclass
class CompleteResult(ToolResult):
    pass
