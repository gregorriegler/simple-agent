from simple_agent.application.display import Display
from simple_agent.application.events import AssistantSaidEvent, ToolResultEvent, SessionEndedEvent


class DisplayEventHandler:
    def __init__(self, display: Display):
        self.displays = {"Agent": display}

    def register_display(self, agent_id: str, display: Display) -> None:
        self.displays[agent_id] = display

    def handle_assistant_says(self, event: AssistantSaidEvent) -> None:
        display = self.displays.get(event.agent_id, self.displays["Agent"])
        display.assistant_says(event.message)

    def handle_tool_result(self, event: ToolResultEvent) -> None:
        display = self.displays.get(event.agent_id, self.displays["Agent"])
        display.tool_result(event.result)

    def handle_session_ended(self, event: SessionEndedEvent) -> None:
        display = self.displays.get(event.agent_id, self.displays["Agent"])
        display.exit()
