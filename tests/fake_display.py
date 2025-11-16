from simple_agent.application.display import AgentDisplay, AgentDisplayHub


class FakeDisplay(AgentDisplayHub):

    def __init__(self, display_factory=None):
        super().__init__()
        self._display_factory = display_factory

    def register_display(self, agent_id: str, display: AgentDisplay) -> None:
        self._register_agent(agent_id, display)

    def _create_display(self, agent_id: str, agent_name: str | None, indent_level: int | None) -> AgentDisplay | None:
        if not self._display_factory:
            return None
        return self._display_factory(agent_id, agent_name, indent_level)
