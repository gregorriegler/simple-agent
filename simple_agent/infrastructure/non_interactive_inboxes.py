from simple_agent.application.agent_id import AgentId
from simple_agent.application.inbox import Inbox


class NonInteractiveInboxes:
    """Nobody types: every agent works off what it was given and then ends."""

    def for_agent(self, agent_id: AgentId) -> Inbox:
        return self.assign(agent_id, Inbox())

    def assign(self, agent_id: AgentId, inbox: Inbox) -> Inbox:
        inbox.close()
        return inbox

    def close(self) -> None:
        pass
