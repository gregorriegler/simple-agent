import json
from pathlib import Path

from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_serializer import EventSerializer
from simple_agent.application.events import AgentEvent
from simple_agent.logging_config import get_logger

logger = get_logger(__name__)


class FileEventStore:
    def __init__(self, session_root: Path):
        self._session_root = session_root
        self._events_file = session_root / "events.jsonl"

    def persist(self, event: AgentEvent) -> None:
        self._session_root.mkdir(parents=True, exist_ok=True)
        try:
            data = EventSerializer.to_dict(event)
            line = json.dumps(data, ensure_ascii=False)
            with open(self._events_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as error:
            logger.warning("Could not persist event: %s", error)

    def load_events(self, agent_id: AgentId | None = None) -> list[AgentEvent]:
        all_events = self.load_all_events()
        if agent_id is None:
            return all_events
        return [e for e in all_events if e.agent_id == agent_id]

    def load_all_events(self) -> list[AgentEvent]:
        if not self._events_file.exists():
            return []

        events: list[AgentEvent] = []
        try:
            with open(self._events_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        event = EventSerializer.from_dict(data)
                        events.append(event)
                    except (json.JSONDecodeError, ValueError) as error:
                        logger.warning("Skipping corrupted event line: %s", error)
                        continue
        except Exception as error:
            logger.warning("Could not load events file: %s", error)

        return events
