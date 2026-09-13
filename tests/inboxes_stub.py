import asyncio
from collections.abc import Iterable

from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import EventBus
from simple_agent.application.events import ToolCalledEvent, UserPromptRequestedEvent
from simple_agent.application.inbox import Inbox
from simple_agent.application.inboxes import AgentInboxes


class ScriptedInboxes:
    """A user who answers whichever agent asks for a prompt with the next scripted line.

    Observers stay unanswered unless the script types to them by name."""

    def __init__(
        self,
        event_bus: EventBus,
        inputs: Iterable | None = None,
        typed_while_working: Iterable[str] | None = None,
        silent: Iterable[str] = (),
        typed_to: dict[str, list[str]] | None = None,
    ):
        self._inboxes = AgentInboxes()
        self._inputs = list(inputs) if inputs is not None else []
        self._typed_while_working = list(typed_while_working or [])
        self._silent = set(silent)
        self._typed_to = {name: list(lines) for name, lines in (typed_to or {}).items()}
        event_bus.subscribe(UserPromptRequestedEvent, self._answer)
        event_bus.subscribe(ToolCalledEvent, self._type_while_working)

    def for_agent(self, agent_id: AgentId) -> Inbox:
        return self._inboxes.for_agent(agent_id)

    def assign(self, agent_id: AgentId, inbox: Inbox) -> Inbox:
        return self._inboxes.assign(agent_id, inbox)

    def close(self) -> None:
        self._inboxes.close()

    def _answer(self, event: UserPromptRequestedEvent) -> None:
        agent_id = event.agent_id
        if agent_id.raw in self._typed_to:
            lines = self._typed_to[agent_id.raw]
            if lines:
                self._type(agent_id, lines.pop(0))
            return
        if agent_id.raw.rsplit("/", 1)[-1] in self._silent:
            return
        try:
            line = self._next_line()
        except (KeyboardInterrupt, EOFError):
            self.close()
            return
        self._type(agent_id, line)

    def _type(self, agent_id: AgentId, line: str) -> None:
        """A person needs a moment to type, so the line lands on the next loop tick."""
        asyncio.get_running_loop().call_soon(self.for_agent(agent_id).put, line)

    def _next_line(self) -> str:
        if not self._inputs:
            return ""
        value = self._inputs.pop(0)
        if callable(value):
            try:
                value = value()
            except TypeError:
                value = value("")
        return str(value).strip()

    def _type_while_working(self, event: ToolCalledEvent) -> None:
        typed, self._typed_while_working = self._typed_while_working, []
        for message in typed:
            self.for_agent(event.agent_id).put(message)
