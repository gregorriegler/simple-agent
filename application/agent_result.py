from dataclasses import dataclass

@dataclass
class AgentResult:
    pass

@dataclass
class ContinueResult(AgentResult):
    feedback: str

@dataclass
class CompleteResult(AgentResult):
    summary: str

@dataclass
class InterruptResult(AgentResult):
    pass