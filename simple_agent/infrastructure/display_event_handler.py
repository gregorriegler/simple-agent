from simple_agent.application.display import Display
from simple_agent.application.events import AssistantSaidEvent, ToolResultEvent, SessionEndedEvent, SessionStartedEvent, \
    ToolCalledEvent, UserPromptedEvent


class DisplayEventHandler:
    def __init__(self, display: Display):
        self.displays = {"Agent": display}

    def register_display(self, agent_id: str, display: Display) -> None:
        self.displays[agent_id] = display

    def handle_session_started(self, event: SessionStartedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if event.is_continuation:
            display.continue_session()
        else:
            display.start_new_session()

    def handle_user_prompted(self, event: UserPromptedEvent) -> None:
        display = self.displays.get(event.agent_id)
        display.user_says(event.input_text)

    def handle_assistant_said(self, event: AssistantSaidEvent) -> None:
        display = self.displays.get(event.agent_id)
        display.assistant_says(event.message)

    def handle_tool_called(self, event: ToolCalledEvent) -> None:
        display = self.displays.get(event.agent_id)
        display.tool_call(event.tool)

    def handle_tool_result(self, event: ToolResultEvent) -> None:
        display = self.displays.get(event.agent_id)
        display.tool_result(event.result)

    def handle_session_ended(self, event: SessionEndedEvent) -> None:
        display = self.displays.get(event.agent_id)
        display.exit()
