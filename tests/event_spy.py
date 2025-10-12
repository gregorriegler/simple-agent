from typing import List, Tuple, Any
from dataclasses import fields
from simple_agent.application.events import EventType


class EventSpy:
    def __init__(self):
        self.events: List[Tuple[EventType, Any]] = []

    def record_event(self, event_type: EventType, event_data: Any):
        self.events.append((event_type, event_data))

    def get_events(self, event_type: EventType) -> List[Any]:
        return [event_data for evt_type, event_data in self.events if evt_type == event_type]

    def get_all_events(self) -> List[Tuple[EventType, Any]]:
        return self.events

    def get_events_as_string(self) -> str:
        lines = []
        for event_type, event_data in self.events:
            field_values = []
            for field in fields(event_data):
                if field.name != "agent_id":
                    field_values.append(str(getattr(event_data, field.name)))
            lines.append(f"{event_data.agent_id}: {event_type.value:>21}: {' '.join(field_values)}")
        return "\n".join(lines)

    def clear(self):
        self.events.clear()
