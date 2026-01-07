from dataclasses import dataclass


@dataclass(frozen=True)
class AgentSwitch:
    agent_type: str
