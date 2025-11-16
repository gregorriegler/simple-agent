from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_display import TextualDisplay
from simple_agent.infrastructure.textual.textual_messages import (
    AddSubagentTabMessage,
    RemoveSubagentTabMessage,
)


class TextualSubagentDisplay(TextualDisplay):
    def __init__(self, app: TextualApp, agent_id: str, agent_name: str):
        super().__init__(app, agent_id, agent_name)
        self._create_tab()

    def _create_tab(self):
        if self.app and self.app.is_running:
            tab_title = self.agent_name or self.agent_id.split('/')[-1]
            self.app.post_message(AddSubagentTabMessage(self.agent_id, tab_title))

    def exit(self):
        if self.app and self.app.is_running:
            self.app.post_message(RemoveSubagentTabMessage(self.agent_id))
