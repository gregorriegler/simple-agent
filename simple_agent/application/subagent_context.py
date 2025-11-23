from typing import TYPE_CHECKING

from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.events import AgentCreatedEvent, AgentFinishedEvent
from simple_agent.application.llm import Messages
from simple_agent.application.agent_type import AgentType

if TYPE_CHECKING:
    from simple_agent.application.agent_factory import AgentFactory


class SubagentContext:
    def __init__(
        self,
        agent_factory: "AgentFactory",
        create_subagent_input,
        indent_level: int,
        agent_id: AgentId,
        event_bus: EventBus
    ):
        self.agent_factory = agent_factory
        self.create_input = create_subagent_input
        self.indent_level = indent_level
        self.agent_id = agent_id
        self._event_bus = event_bus

    def notify_subagent_created(self, subagent_id: AgentId, subagent_name: str) -> None:
        self._event_bus.publish(AgentCreatedEvent(self.agent_id, subagent_id, subagent_name, self.indent_level))

    def notify_subagent_finished(self, subagent_id: AgentId) -> None:
        self._event_bus.publish(AgentFinishedEvent(self.agent_id, subagent_id))

    def spawn_subagent(self, agent_type: AgentType, task_description: str):
        user_input = self.create_input()
        user_input.stack(task_description)

        subagent = self.agent_factory(
            agent_type,
            self.agent_id,
            self.indent_level,
            user_input,
            Messages()
        )

        self.notify_subagent_created(subagent.agent_id, subagent.agent_name)

        try:
            result = subagent.start()
            return result
        finally:
            self.notify_subagent_finished(subagent.agent_id)
