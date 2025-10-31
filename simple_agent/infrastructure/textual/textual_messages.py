from textual.message import Message


class UserSaysMessage(Message):
    def __init__(self, log_id: str, content: str) -> None:
        super().__init__()
        self.log_id = log_id
        self.content = content


class AssistantSaysMessage(Message):
    def __init__(self, log_id: str, content: str, is_first_line: bool = False) -> None:
        super().__init__()
        self.log_id = log_id
        self.content = content
        self.is_first_line = is_first_line


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


class SessionStatusMessage(Message):
    def __init__(self, log_id: str, status: str) -> None:
        super().__init__()
        self.log_id = log_id
        self.status = status


class AddSubagentTabMessage(Message):
    def __init__(self, agent_id: str, tab_title: str) -> None:
        super().__init__()
        self.agent_id = agent_id
        self.tab_title = tab_title


class RemoveSubagentTabMessage(Message):
    def __init__(self, agent_id: str) -> None:
        super().__init__()
        self.agent_id = agent_id
