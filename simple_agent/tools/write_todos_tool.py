from simple_agent.application.agent_id import AgentId
from simple_agent.application.todos import Todos
from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus

from .base_tool import BaseTool


class WriteTodosTool(BaseTool):
    name = "write-todos"
    description = (
        "Organize your work in TODOs. Use this tool to create or update those TODOs"
    )
    arguments = ToolArguments(
        header=[],
        body=ToolArgument(
            name="content",
            type="string",
            required=True,
            description="Markdown checklist to represent the todos. Use - [ ] for todo, - [ ] **doing** for in-progress, - [x] for done",
        ),
    )
    examples = [
        {
            "content": "- [ ] Item 1",
            "result": "Updated TODOS",
        },
        {
            "content": "- [ ] Feature exploration\n- [ ] **Implementing tool**\n- [x] Initial setup"
        },
    ]

    def __init__(self, todos: Todos, agent_id: AgentId):
        super().__init__()
        self._todos = todos
        self._agent_id = agent_id

    async def execute(self, call):
        body = str(call.named_arguments.get("content", ""))
        if not body or not body.strip():
            return SingleToolResult(
                "No todo content provided", status=ToolResultStatus.FAILURE
            )

        self._todos.write(self._agent_id, body)
        return SingleToolResult("Updated TODOS")
