import pytest

from simple_agent.application.agent_id import AgentId
from simple_agent.infrastructure.subscribe_events import subscribe_events
from simple_agent.infrastructure.textual.textual_app import TextualApp


class FakeEventBus:
    def __init__(self) -> None:
        self._handlers = {}

    def subscribe(self, event_type, handler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event) -> None:
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event)


class FakeSessionStorage:
    def load(self):
        return []

    def save(self, messages):
        return None


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


class FakeEventLogger:
    def log_event(self, event) -> None:
        return None


class FakeTodoCleanup:
    def cleanup_all_todos(self) -> None:
        return None

    def cleanup_todos_for_agent(self, agent_id) -> None:
        return None


class StubTool:
    def header(self) -> str:
        return "Tool Call\nInput: example"


@pytest.fixture
def textual_harness():
    event_bus = FakeEventBus()
    session_storage = FakeSessionStorage()
    user_input = FakeUserInput()
    app = TextualApp(user_input, AgentId("Agent"))

    subscribe_events(event_bus, FakeEventLogger(), FakeTodoCleanup(), app)

    return event_bus, session_storage, user_input, app
