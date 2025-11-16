from simple_agent.application.display import AgentDisplay


class FakeDisplay:

    def __init__(self, display_factory=None):
        self._agents: dict[str, AgentDisplay] = {}
        self._display_factory = display_factory

    def register_display(self, agent_id: str, display: AgentDisplay) -> None:
        self._agents[agent_id] = display

    def agent_created(self, event) -> None:
        if not self._display_factory:
            return
        if event.subagent_id in self._agents:
            return
        display = self._display_factory(event.subagent_id, event.subagent_name, event.indent_level)
        self.register_display(event.subagent_id, display)

    def start_session(self, event) -> None:
        agent = self._agents.get(event.agent_id)
        if not agent:
            return
        if getattr(event, "is_continuation", False):
            agent.continue_session()
        else:
            agent.start_new_session()

    def wait_for_input(self, event) -> None:
        display = self._agents.get(event.agent_id)
        if display:
            display.waiting_for_input()

    def user_says(self, event) -> None:
        display = self._agents.get(event.agent_id)
        if display:
            display.user_says(event.input_text)

    def assistant_says(self, event) -> None:
        display = self._agents.get(event.agent_id)
        if display:
            display.assistant_says(event.message)

    def tool_call(self, event) -> None:
        display = self._agents.get(event.agent_id)
        if display:
            display.tool_call(event.call_id, event.tool)

    def tool_result(self, event) -> None:
        display = self._agents.get(event.agent_id)
        if display:
            display.tool_result(event.call_id, event.result)

    def interrupted(self, event) -> None:
        display = self._agents.get(event.agent_id)
        if display:
            display.interrupted()

    def exit(self, event) -> None:
        display = self._agents.get(event.agent_id)
        if display:
            display.exit()
            self._agents.pop(event.agent_id, None)
