from textual.message import Message

from simple_agent.application.agent_id import AgentId


class AddSubagentTabMessage(Message):
    def __init__(self, agent_id: AgentId, tab_title: str) -> None:
        super().__init__()
        self.agent_id = agent_id
        self.tab_title = tab_title


class RemoveAgentTabMessage(Message):
    def __init__(self, agent_id: AgentId) -> None:
        super().__init__()
        self.agent_id = agent_id


class DomainEventMessage(Message):
    def __init__(self, event) -> None:
        super().__init__()
        self.event = event
