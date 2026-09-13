from typing import Protocol

from .agent_id import AgentId
from .inbox import Inbox


class Inboxes(Protocol):
    """One inbox per agent."""

    def for_agent(self, agent_id: AgentId) -> Inbox: ...

    def close(self) -> None: ...


class AgentInboxes:
    """One inbox per agent; a message typed on an agent's tab goes to that agent."""

    def __init__(self):
        self._inboxes: dict[AgentId, Inbox] = {}
        self._closed = False

    def for_agent(self, agent_id: AgentId) -> Inbox:
        inbox = self._inboxes.get(agent_id)
        if inbox is None:
            inbox = self.assign(agent_id, Inbox())
        return inbox

    def assign(self, agent_id: AgentId, inbox: Inbox) -> Inbox:
        if self._closed:
            inbox.close()
        self._inboxes[agent_id] = inbox
        return inbox

    def submit_input(self, agent_id: AgentId, message: str) -> None:
        self.for_agent(agent_id).put(message)

    def close(self) -> None:
        self._closed = True
        for inbox in self._inboxes.values():
            inbox.close()
