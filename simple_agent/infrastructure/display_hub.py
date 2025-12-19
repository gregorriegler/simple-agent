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

    def agent_created(self, event) -> None:
        name = getattr(event, "agent_name", None)
        model = getattr(event, "model", "")
        existing = self._agent_for(event.agent_id)
        if not existing:
            created = self._create_display(event.agent_id, name, model)
            if created:
                self._register_agent(event.agent_id, created)

    def exit(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if not agent:
            return
        agent.exit()
        self._on_agent_removed(event.agent_id, agent)
