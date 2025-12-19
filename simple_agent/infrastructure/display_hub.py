from simple_agent.application.agent_id import AgentId
from simple_agent.application.display import AgentDisplay, Display


class AgentDisplayHub(Display):

    def __init__(self):
        self._agents: dict[AgentId, AgentDisplay] = {}

    def _create_display(self, agent_id: AgentId, agent_name: str | None, model: str = "") -> AgentDisplay | None:
        raise NotImplementedError

    def _on_agent_removed(self, agent_id: AgentId, agent: AgentDisplay) -> None:
        self._agents.pop(agent_id, None)

    def _agent_for(self, agent_id: AgentId) -> AgentDisplay | None:
        return self._agents.get(agent_id)

    def _register_agent(self, agent_id: AgentId, display: AgentDisplay) -> None:
        self._agents[agent_id] = display

    def _ensure_agent(self, agent_id: AgentId, agent_name: str | None = None, model: str = "") -> AgentDisplay | None:
        existing = self._agent_for(agent_id)
        if existing:
            return existing
        created = self._create_display(agent_id, agent_name, model)
        if created:
            self._register_agent(agent_id, created)
        return created

    def agent_created(self, event) -> None:
        self._ensure_agent(event.agent_id, getattr(event, "agent_name", None), getattr(event, "model", ""))

    def exit(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if not agent:
            return
        agent.exit()
        self._on_agent_removed(event.agent_id, agent)
