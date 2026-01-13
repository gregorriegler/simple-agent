from textual.containers import Vertical

from simple_agent.application.agent_id import AgentId
from simple_agent.application.tool_results import ToolResult
from simple_agent.infrastructure.textual.resizable_container import (
    ResizableHorizontal,
    ResizableVertical,
)
from simple_agent.infrastructure.textual.smart_input.autocomplete.autocomplete import (
    SuggestionProvider,
)
from simple_agent.infrastructure.textual.smart_input.smart_input import SmartInput
from simple_agent.infrastructure.textual.widgets.chat_log import ChatLog
from simple_agent.infrastructure.textual.widgets.todo_view import TodoView
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog


class AgentWorkspace(Vertical):
    """
    A compound widget that displays the layout for an agent:
    - Top: Split view with Chat history (left) and Tool execution log (right)
    - Bottom: SmartInput
    """

    def __init__(
        self,
        agent_id: AgentId,
        log_id: str,
        tool_results_id: str,
        suggestion_provider: SuggestionProvider,
        **kwargs,
    ):
        self.agent_id = agent_id
        self.chat_log = ChatLog(id=f"{log_id}-scroll", classes="left-panel-top")
        self.todo_view = TodoView(
            agent_id,
            markdown_id=f"{log_id}-todos",
            id=f"{log_id}-secondary",
            classes="left-panel-bottom",
        )

        self.left_panel = ResizableVertical(
            self.chat_log, self.todo_view, id="left-panel"
        )
        self.left_panel.set_bottom_visibility(self.todo_view.has_content)

        self.tool_log = ToolLog(id=tool_results_id)

        self.split_view = ResizableHorizontal(self.left_panel, self.tool_log)

        self.smart_input = SmartInput(
            provider=suggestion_provider,
            id=f"input-{agent_id.for_ui()}",
            classes="smart-input",
        )

        super().__init__(self.split_view, self.smart_input, **kwargs)

    def refresh_todos(self) -> None:
        self.todo_view.refresh_content()
        self.left_panel.set_bottom_visibility(self.todo_view.has_content)

    def on_tool_call(self, call_id: str, message: str) -> None:
        self.tool_log.add_tool_call(call_id, message)

    def on_tool_result(self, call_id: str, result: ToolResult) -> None:
        self.tool_log.add_tool_result(call_id, result)
        self.refresh_todos()

    def on_tool_cancelled(self, call_id: str) -> None:
        self.tool_log.add_tool_cancelled(call_id)
        self.refresh_todos()

    def write_message(self, message: str) -> None:
        self.chat_log.write(message)

    def add_user_message(self, message: str) -> None:
        self.chat_log.add_user_message(message)

    def add_assistant_message(self, message: str, agent_name: str) -> None:
        self.chat_log.add_assistant_message(message, agent_name)

    def clear(self) -> None:
        self.chat_log.remove_children()
        self.tool_log.clear()
        self.todo_view.update("")
        self.left_panel.set_bottom_visibility(False)
        self.smart_input.clear()
