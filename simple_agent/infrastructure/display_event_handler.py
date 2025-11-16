from simple_agent.application.display import Display
from simple_agent.application.events import AssistantSaidEvent, ToolResultEvent, SessionEndedEvent, \
    SessionInterruptedEvent, SessionStartedEvent, ToolCalledEvent, UserPromptedEvent, UserPromptRequestedEvent, \
    AgentCreatedEvent


class AllDisplays:
    def __init__(self, display_factory=None):
        self.displays = {}
        self._display_factory = display_factory

    def register_display(self, agent_id: str, display: Display) -> None:
        self.displays[agent_id] = display

    def agent_created(self, event: AgentCreatedEvent) -> None:
        if not self._display_factory:
            return
        if event.subagent_id in self.displays:
            return
        display = self._display_factory(event.subagent_id, event.subagent_name, event.indent_level)
        self.register_display(event.subagent_id, display)

    def start_session(self, event: SessionStartedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        if event.is_continuation:
            display.continue_session()
        else:
            display.start_new_session()

    def wait_for_input(self, event: UserPromptRequestedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.waiting_for_input()

    def user_says(self, event: UserPromptedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.user_says(event.input_text)

    def assistant_says(self, event: AssistantSaidEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.assistant_says(event.message)

    def tool_call(self, event: ToolCalledEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.tool_call(event.call_id, event.tool)

    def tool_result(self, event: ToolResultEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.tool_result(event.call_id, event.result)

    def interrupted(self, event: SessionInterruptedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.interrupted()

    def exit(self, event: SessionEndedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.exit()
        del self.displays[event.agent_id]
