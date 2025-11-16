from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_display import TextualDisplay
from simple_agent.infrastructure.textual.textual_messages import RemoveSubagentTabMessage


class TextualSubagentDisplay(TextualDisplay):
    def __init__(self, app: TextualApp, agent_id: str, agent_name: str):
        super().__init__(app, agent_id, agent_name)

    def exit(self):
        if self.app and self.app.is_running:
            self.app.post_message(RemoveSubagentTabMessage(self.agent_id))
