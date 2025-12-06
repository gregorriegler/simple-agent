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

    def start_session(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if not agent:
            return
        if getattr(event, "is_continuation", False):
            agent.continue_session()
        else:
            agent.start_new_session()

    def wait_for_input(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if agent:
            agent.waiting_for_input()

    def user_says(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if agent:
            agent.user_says(event.input_text)

    def assistant_says(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if agent:
            agent.assistant_says(event.message)
    def assistant_responded(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if agent:
            agent.assistant_responded(event.model, event.token_count, event.max_tokens)

    def tool_call(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if agent:
            agent.tool_call(event.call_id, event.tool)

    def tool_result(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if agent:
            agent.tool_result(event.call_id, event.result)

    def interrupted(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if agent:
            agent.interrupted()

    def error_occurred(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if agent:
            agent.error_occurred(event.message)

    def exit(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if not agent:
            return
        agent.exit()
        self._on_agent_removed(event.agent_id, agent)
