from dataclasses import dataclass

@dataclass
class AgentResult:
    feedback: str
    pass
    def __str__(self) : return self.feedback

@dataclass
class ContinueResult(AgentResult):
    pass

@dataclass
class CompleteResult(AgentResult):
    pass

@dataclass
class InterruptResult(AgentResult):
    pass
