from typing import TYPE_CHECKING

from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.events import SubagentCreatedEvent, SubagentFinishedEvent

if TYPE_CHECKING:
    from simple_agent.application.agent_factory import AgentFactory


class SubagentContext:
    def __init__(
        self,
        agent_factory: "AgentFactory",
        create_subagent_input,
        indent_level: int,
        agent_id: str,
        event_bus: EventBus
    ):
        self.create_agent = agent_factory
        self._create_subagent_input = create_subagent_input
        self.indent_level = indent_level
        self.agent_id = agent_id
        self._event_bus = event_bus

    @property
    def create_input(self):
        return self._create_subagent_input

    def notify_subagent_created(self, subagent_id: str, subagent_name: str) -> None:
        self._event_bus.publish(SubagentCreatedEvent(self.agent_id, subagent_id, subagent_name, self.indent_level))

    def notify_subagent_finished(self, subagent_id: str) -> None:
        self._event_bus.publish(SubagentFinishedEvent(self.agent_id, subagent_id))
