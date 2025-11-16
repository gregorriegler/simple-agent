from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_display import TextualDisplay


class TextualSubagentDisplay(TextualDisplay):
    def __init__(self, app: TextualApp, agent_id: str, agent_name: str):
        super().__init__(app, agent_id, agent_name)
