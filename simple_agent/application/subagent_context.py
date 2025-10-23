from simple_agent.application.agent_factory import CreateAgent


class SubagentContext:
    def __init__(
        self,
        create_agent: CreateAgent,
        indent_level: int,
        agent_id: str
    ):
        self.create_agent = create_agent
        self.indent_level = indent_level
        self.agent_id = agent_id

    @property
    def create_display(self):
        return self.create_agent.create_subagent_display

    @property
    def create_input(self):
        return self.create_agent.create_subagent_input
