from simple_agent.application.agent_id import AgentId
from simple_agent.application.todos import Todos


class FileTodos(Todos):
    def read(self, agent_id: AgentId) -> str:
        filename = agent_id.todo_filename()
        if not filename.exists():
            return ""
        return filename.read_text(encoding="utf-8").strip()

    def write(self, agent_id: AgentId, todos: str) -> None:
        agent_id.todo_filename().write_text(todos, encoding="utf-8")
