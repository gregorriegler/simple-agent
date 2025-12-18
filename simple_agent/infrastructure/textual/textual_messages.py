from textual.message import Message

from simple_agent.application.agent_id import AgentId


class AssistantSaysMessage(Message):
    def __init__(self, log_id: str, content: str) -> None:
        super().__init__()
        self.log_id = log_id
        self.content = content


class ToolCallMessage(Message):
    def __init__(self, tool_results_id: str, call_id: str, tool_str: str) -> None:
        super().__init__()
        self.tool_results_id = tool_results_id
        self.call_id = call_id
        self.tool_str = tool_str


class ToolResultMessage(Message):
    def __init__(self, tool_results_id: str, call_id: str, result: 'ToolResult') -> None:
        super().__init__()
        self.tool_results_id = tool_results_id
        self.call_id = call_id
        self.result = result


class ToolCancelledMessage(Message):
    def __init__(self, tool_results_id: str, call_id: str) -> None:
        super().__init__()
        self.tool_results_id = tool_results_id
        self.call_id = call_id


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
