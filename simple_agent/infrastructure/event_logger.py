import logging
from pathlib import Path
from simple_agent.application.events import AgentEvent


class EventLogger:

    def __init__(self, log_file_path: str):
        self.log_file_path = Path(log_file_path)
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger('event_logger')
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        file_handler = logging.FileHandler(self.log_file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def log_event(self, event: AgentEvent):
        event_type = type(event).__name__
        event_data = {k: v for k, v in event.__dict__.items() if not k.startswith('_')}
        self.logger.info(f"{event_type}: {event_data}")
