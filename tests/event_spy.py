from typing import List, Type
from dataclasses import fields
from simple_agent.application.events import AgentEvent


class EventSpy:
    def __init__(self):
        self.events: List[AgentEvent] = []

    def record_event(self, event: AgentEvent):
        self.events.append(event)

    def assert_occured(self, event_type: Type[AgentEvent], times=1):
        actual_times = len(self.get_events(event_type))
        assert actual_times == times, (
            "{0} was expected to have occured {1} times, but actually occured {2} times".format(
                event_type.__name__, times, actual_times
            )
        )

    def assert_never_occured(self, event_type: Type[AgentEvent]):
        assert not self.get_events(event_type), (
            event_type.__name__ + " should have never occured"
        )

    def assert_event_occured(self, expected_event: AgentEvent, times: int = 1):
        def matches(actual: AgentEvent) -> bool:
            if type(actual) is not type(expected_event):
                return False
            for field in fields(expected_event):
                expected_val = getattr(expected_event, field.name)
                if expected_val is None or expected_val == "":
                    # Treat None or empty string as "don't care" for testing convenience
                    continue
                if expected_val != getattr(actual, field.name):
                    return False
            return True

        actual_times = len([e for e in self.events if matches(e)])
        assert actual_times == times, (
            f"Expected {expected_event} to occur {times} times, but found {actual_times} matches"
        )

    def get_events(self, event_type: Type[AgentEvent]) -> List[AgentEvent]:
        return [event for event in self.events if isinstance(event, event_type)]

    def get_all_events(self) -> List[AgentEvent]:
        return self.events

    def get_events_as_string(self) -> str:
        lines = []
        for event in self.events:
            field_values = []
            for field in fields(event):
                if field.name != "agent_id":
                    field_values.append(str(getattr(event, field.name)))
            lines.append(
                f"{event.agent_id}: {event.event_name:>21}: {' '.join(field_values)}"
            )
        return "\n".join(lines)

    def clear(self):
        self.events.clear()
