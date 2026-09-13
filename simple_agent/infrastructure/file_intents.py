from simple_agent.application.agent_id import AgentId
from simple_agent.application.intent import Intents


class FileIntents(Intents):
    def read(self, agent_id: AgentId) -> str:
        filename = agent_id.intent_filename()
        if not filename.exists():
            return ""
        return filename.read_text(encoding="utf-8").strip()

    def write(self, agent_id: AgentId, intent: str) -> None:
        agent_id.intent_filename().write_text(intent, encoding="utf-8")
