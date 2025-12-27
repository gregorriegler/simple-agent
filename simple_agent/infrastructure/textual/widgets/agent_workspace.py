from typing import Callable

from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.textual.resizable_container import ResizableHorizontal, ResizableVertical
from simple_agent.infrastructure.textual.widgets.chat_log import ChatLog
from simple_agent.infrastructure.textual.widgets.todo_view import TodoView
from simple_agent.infrastructure.textual.widgets.tool_log import ToolLog

class AgentWorkspace(ResizableHorizontal):
    """
    A compound widget that displays the 3-pane layout for an agent:
    - Left Panel: Chat history (top) and Todo list (bottom)
    - Right Panel: Tool execution log
    """

    def __init__(
        self,
        agent_id: AgentId,
        log_id: str,
        tool_results_id: str,
        on_refresh_todos: Callable[[], None],
        **kwargs
    ):
        self.chat_log = ChatLog(id=f"{log_id}-scroll", classes="left-panel-top")
        self.todo_view = TodoView(
            agent_id,
            markdown_id=f"{log_id}-todos",
            id=f"{log_id}-secondary",
            classes="left-panel-bottom"
        )

        self.left_panel = ResizableVertical(self.chat_log, self.todo_view, id="left-panel")
        self.left_panel.set_bottom_visibility(self.todo_view.has_content)

        self.tool_log = ToolLog(id=tool_results_id, on_refresh_todos=on_refresh_todos)

        super().__init__(self.left_panel, self.tool_log, **kwargs)

    def refresh_todos(self) -> None:
        self.todo_view.refresh_content()
        self.left_panel.set_bottom_visibility(self.todo_view.has_content)
