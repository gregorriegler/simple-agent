import logging

from simple_agent.application.events import AgentEvent


class EventLogger:
    def __init__(self):
        self.logger = logging.getLogger("simple_agent.events")

    def log_event(self, event: AgentEvent):
        event_type = type(event).__name__
        event_data = {
            k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
            for k, v in event.__dict__.items()
            if not k.startswith("_")
        }
        self.logger.info(f"{event_type}: {event_data}")
