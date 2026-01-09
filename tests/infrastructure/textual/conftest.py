from pathlib import Path

import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.llm import Messages
from simple_agent.infrastructure.event_logger import EventLogger
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from simple_agent.infrastructure.subscribe_events import subscribe_events
from simple_agent.infrastructure.textual.textual_app import TextualApp


class FakeSessionStorage:
    def load_messages(self, agent_id):
        return Messages()

    def save_messages(self, agent_id, messages):
        return None

    def session_root(self):
        return Path(".")


class FakeUserInput:
    def __init__(self) -> None:
        self.submissions = []
        self.closed = False

    async def read_async(self) -> str:
        return ""

    def escape_requested(self) -> bool:
        return False

    def submit_input(self, content: str) -> None:
        self.submissions.append(content)

    def close(self) -> None:
        self.closed = True


class FakeEventLogger(EventLogger):
    def log_event(self, event) -> None:
        return None


class FakeTodoCleanup(FileSystemTodoCleanup):
    def __init__(self):
        super().__init__(Path("."))

    def cleanup_all_todos(self) -> None:
        return None

    def cleanup_todos_for_agent(self, agent_id) -> None:
        return None


class StubTool:
    def header(self) -> str:
        return "Tool Call\nInput: example"


@pytest.fixture
def textual_harness():
    event_bus = SimpleEventBus()
    session_storage = FakeSessionStorage()
    user_input = FakeUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    subscribe_events(event_bus, FakeEventLogger(), FakeTodoCleanup(), app)

    return event_bus, session_storage, user_input, app
