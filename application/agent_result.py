from dataclasses import dataclass

@dataclass
class AgentResult:
    pass

@dataclass
class ContinueResult(AgentResult):
    feedback: str

    def __str__(self) : return self.feedback

@dataclass
class CompleteResult(AgentResult):
    summary: str

@dataclass
class InterruptResult(AgentResult):
    pass
