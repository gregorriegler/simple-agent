from simple_agent.application.agent_id import AgentId
from simple_agent.application.intent import Intent


class FileIntent(Intent):
    def __init__(self, agent_id: AgentId):
        self._agent_id = agent_id

    def read(self) -> str:
        filename = self._agent_id.intent_filename()
        if not filename.exists():
            return ""
        return filename.read_text(encoding="utf-8").strip()
