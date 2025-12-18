from textual.message import Message

from simple_agent.application.agent_id import AgentId


class SessionStatusMessage(Message):
    def __init__(self, log_id: str, status: str) -> None:
        super().__init__()
        self.log_id = log_id
        self.status = status


class AddSubagentTabMessage(Message):
    def __init__(self, agent_id: AgentId, tab_title: str) -> None:
        super().__init__()
        self.agent_id = agent_id
        self.tab_title = tab_title


class RemoveAgentTabMessage(Message):
    def __init__(self, agent_id: AgentId) -> None:
        super().__init__()
        self.agent_id = agent_id


class RefreshTodosMessage(Message):
    def __init__(self, agent_id: AgentId) -> None:
        super().__init__()
        self.agent_id = agent_id


class UpdateTabTitleMessage(Message):
    def __init__(self, agent_id: AgentId, title: str) -> None:
        super().__init__()
        self.agent_id = agent_id
        self.title = title


class DomainEventMessage(Message):
    def __init__(self, event) -> None:
        super().__init__()
        self.event = event
