from typing import Protocol

from simple_agent.application.tool_library import ToolResult


class Display(Protocol):

    def agent_created(self, event) -> None:
        ...

    def start_session(self, event) -> None:
        ...

    def wait_for_input(self, event) -> None:
        ...

    def user_says(self, event) -> None:
        ...

    def assistant_says(self, event) -> None:
        ...

    def tool_call(self, event) -> None:
        ...

    def tool_result(self, event) -> None:
        ...

    def interrupted(self, event) -> None:
        ...

    def exit(self, event) -> None:
        ...


class AgentDisplay(Protocol):

    def assistant_says(self, message) -> None:
        ...

    def user_says(self, message) -> None:
        ...

    def tool_call(self, call_id: str, tool) -> None:
        ...

    def tool_result(self, call_id: str, result: ToolResult) -> None:
        ...

    def continue_session(self) -> None:
        ...

    def start_new_session(self) -> None:
        ...

    def waiting_for_input(self) -> None:
        ...

    def interrupted(self) -> None:
        ...

    def exit(self) -> None:
        ...


class AgentDisplayHub(Display):

    def __init__(self):
        self._agents: dict[str, AgentDisplay] = {}

    def _create_display(self, agent_id: str, agent_name: str | None, indent_level: int | None) -> AgentDisplay | None:
        raise NotImplementedError

    def _on_agent_removed(self, agent_id: str, agent: AgentDisplay) -> None:
        self._agents.pop(agent_id, None)

    def _agent_for(self, agent_id: str) -> AgentDisplay | None:
        return self._agents.get(agent_id)

    def _register_agent(self, agent_id: str, display: AgentDisplay) -> None:
        self._agents[agent_id] = display

    def _ensure_agent(self, agent_id: str, agent_name: str | None = None, indent_level: int | None = None) -> AgentDisplay | None:
        existing = self._agent_for(agent_id)
        if existing:
            return existing
        created = self._create_display(agent_id, agent_name, indent_level)
        if created:
            self._register_agent(agent_id, created)
        return created

    def agent_created(self, event) -> None:
        self._ensure_agent(event.subagent_id, getattr(event, "subagent_name", None), getattr(event, "indent_level", None))

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

    def exit(self, event) -> None:
        agent = self._agent_for(event.agent_id)
        if not agent:
            return
        agent.exit()
        self._on_agent_removed(event.agent_id, agent)


class DummyDisplay(AgentDisplay):
    def assistant_says(self, message) -> None:
        pass
    def user_says(self, message) -> None:
        pass
    def tool_call(self, call_id: str, tool) -> None:
        pass
    def tool_result(self, call_id: str, result: ToolResult) -> None:
        pass
    def continue_session(self) -> None:
        pass
    def start_new_session(self) -> None:
        pass
    def waiting_for_input(self) -> None:
        pass
    def interrupted(self) -> None:
        pass
    def exit(self) -> None:
        pass
