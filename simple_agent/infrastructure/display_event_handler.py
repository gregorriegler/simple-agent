from simple_agent.application.display import Display
from simple_agent.application.events import AssistantSaidEvent, ToolResultEvent, SessionEndedEvent, \
    SessionInterruptedEvent, SessionStartedEvent, ToolCalledEvent, UserPromptedEvent, UserPromptRequestedEvent


class DisplayEventHandler:
    def __init__(self, display: Display):
        self.displays = {"Agent": display}

    def register_display(self, agent_id: str, display: Display) -> None:
        self.displays[agent_id] = display

    def handle_session_started(self, event: SessionStartedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        if event.is_continuation:
            display.continue_session()
        else:
            display.start_new_session()

    def handle_user_prompt_requested(self, event: UserPromptRequestedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.waiting_for_input()

    def handle_user_prompted(self, event: UserPromptedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.user_says(event.input_text)

    def handle_assistant_said(self, event: AssistantSaidEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.assistant_says(event.message)

    def handle_tool_called(self, event: ToolCalledEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.tool_call(event.call_id, event.tool)

    def handle_tool_result(self, event: ToolResultEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.tool_result(event.call_id, event.result)

    def handle_session_interrupted(self, event: SessionInterruptedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.interrupted()

    def handle_session_ended(self, event: SessionEndedEvent) -> None:
        display = self.displays.get(event.agent_id)
        if not display:
            return
        display.exit()
