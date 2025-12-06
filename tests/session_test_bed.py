from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AssistantRespondedEvent,
    AssistantSaidEvent,
    AgentStartedEvent,
    ErrorEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.application.llm_stub import create_llm_stub, StubLLMProvider
from simple_agent.application.session import Session
from simple_agent.application.todo_cleanup import NoOpTodoCleanup
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from simple_agent.infrastructure.claude.claude_client import ClaudeClientError
from tests.event_spy import EventSpy
from tests.fake_display import FakeDisplay
from tests.print_spy import IOSpy
from tests.session_storage_stub import SessionStorageStub
from tests.system_prompt_generator_test import GroundRulesStub
from tests.test_helpers import create_session_args
from tests.test_tool_library import ToolLibraryFactoryStub
from tests.user_input_stub import UserInputStub


class SessionTestResult:
    def __init__(self, event_spy: EventSpy, error_events: list, session_storage: SessionStorageStub):
        self.events = event_spy
        self.error_events = error_events
        self.saved_messages = session_storage.saved

    def as_approval_string(self) -> str:
        return f"# Events\n{self.events.get_events_as_string()}\n\n# Saved messages:\n{self.saved_messages}"


class SessionTestBed:
    def __init__(self):
        self._llm = lambda m: ""
        self._user_inputs = ["\n"]
        self._start_message = "test message"
        self._escape_hits = None
        self._ctrl_c_hits = None
        self._continue_session = False
        self._todo_cleanup = None
        self._custom_event_subscriptions = []

    def with_llm_responses(self, responses: list[str]) -> "SessionTestBed":
        self._llm = create_llm_stub(responses)
        return self

    def with_failing_llm(self, error_message: str) -> "SessionTestBed":
        def failing(messages):
            raise ClaudeClientError(error_message)
        self._llm = failing
        return self

    def with_user_inputs(self, start_message: str, *remaining) -> "SessionTestBed":
        self._start_message = start_message
        self._user_inputs = list(remaining) if remaining else ["\n"]
        return self

    def with_escape_hits(self, hits: list[bool]) -> "SessionTestBed":
        self._escape_hits = hits
        return self

    def with_ctrl_c_hits(self, hits: list[bool]) -> "SessionTestBed":
        self._ctrl_c_hits = hits
        return self

    def with_todo_cleanup(self, cleanup) -> "SessionTestBed":
        self._todo_cleanup = cleanup
        return self

    def continuing_session(self) -> "SessionTestBed":
        self._continue_session = True
        return self

    def on_event(self, event_type, handler) -> "SessionTestBed":
        self._custom_event_subscriptions.append((event_type, handler))
        return self

    def run(self) -> SessionTestResult:
        event_bus = SimpleEventBus()
        display = FakeDisplay()
        io_spy = IOSpy(self._user_inputs, self._escape_hits)
        user_input = UserInputStub(io=io_spy)
        session_storage = SessionStorageStub()
        todo_cleanup = self._todo_cleanup if self._todo_cleanup is not None else NoOpTodoCleanup()

        error_events = []
        event_bus.subscribe(ErrorEvent, lambda e: error_events.append(e))

        event_spy = EventSpy()
        tracked_events = [
            SessionStartedEvent,
            UserPromptRequestedEvent,
            UserPromptedEvent,
            AssistantSaidEvent,
            AssistantRespondedEvent,
            ToolCalledEvent,
            ToolResultEvent,
            SessionInterruptedEvent,
            SessionEndedEvent,
        ]
        for event_type in tracked_events:
            event_bus.subscribe(event_type, event_spy.record_event)

        event_bus.subscribe(AssistantSaidEvent, display.assistant_says)
        event_bus.subscribe(ToolCalledEvent, display.tool_call)
        event_bus.subscribe(ToolResultEvent, display.tool_result)
        event_bus.subscribe(SessionStartedEvent, display.start_session)
        event_bus.subscribe(SessionInterruptedEvent, display.interrupted)
        event_bus.subscribe(SessionEndedEvent, display.exit)
        event_bus.subscribe(AgentStartedEvent, display.agent_created)

        for event_type, handler in self._custom_event_subscriptions:
            event_bus.subscribe(event_type, handler)

        tool_library_factory = ToolLibraryFactoryStub(
            self._llm,
            io=io_spy,
            interrupts=[self._ctrl_c_hits],
            event_bus=event_bus,
            all_displays=display
        )

        session = Session(
            event_bus=event_bus,
            session_storage=session_storage,
            tool_library_factory=tool_library_factory,
            agent_library=BuiltinAgentLibrary(),
            user_input=user_input,
            todo_cleanup=todo_cleanup,
            llm_provider=StubLLMProvider.for_testing(self._llm)
        )

        session.run(
            create_session_args(self._continue_session, start_message=self._start_message),
            AgentId("Agent"),
            _create_test_agent_definition()
        )

        return SessionTestResult(event_spy, error_events, session_storage)


def _create_test_agent_definition():
    return AgentDefinition(
        AgentId("Agent"),
        """---
name: Agent
---""",
        GroundRulesStub("Test system prompt")
    )
