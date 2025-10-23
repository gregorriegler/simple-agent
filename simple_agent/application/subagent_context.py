from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simple_agent.application.agent_factory import AgentFactory


class SubagentContext:
    def __init__(
        self,
        agent_factory: "AgentFactory",
        create_subagent_display,
        create_subagent_input,
        indent_level: int,
        agent_id: str
    ):
        self.create_agent = agent_factory
        self._create_subagent_display = create_subagent_display
        self._create_subagent_input = create_subagent_input
        self.indent_level = indent_level
        self.agent_id = agent_id

    @property
    def create_display(self):
        return self._create_subagent_display

    @property
    def create_input(self):
        return self._create_subagent_input
