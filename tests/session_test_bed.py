from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AgentEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    ErrorEvent,
    ModelChangedEvent,
    SessionClearedEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptedEvent,
    UserPromptRequestedEvent,
)
from simple_agent.application.llm import ChatMessages, LLMResponse, TokenUsage
from simple_agent.application.llm_stub import StubLLMProvider, create_llm_stub
from simple_agent.application.session import Session
from simple_agent.infrastructure.claude.claude_client import ClaudeClientError
from tests.event_spy import EventSpy
from tests.session_storage_stub import SessionStorageStub
from tests.system_prompt_generator_test import GroundRulesStub
from tests.test_helpers import DummyProjectTree, create_session_args
from tests.test_tool_library import ToolLibraryFactoryStub
from tests.user_input_stub import UserInputStub


class CapturingLLM:
    def __init__(self):
        self.captured_messages: list[ChatMessages] = []
        self._responses: list[str] = []
        self._response_index = 0

    @property
    def model(self) -> str:
        return "capturing-model"

    def set_responses(self, responses: list[str]) -> None:
        self._responses = responses
        self._response_index = 0

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        self.captured_messages.append(list(messages))
        content = "Done"
        if self._response_index < len(self._responses):
            content = self._responses[self._response_index]
            self._response_index += 1
        return LLMResponse(
            content=content,
            model=self.model,
            usage=TokenUsage(0, 0, 0),
        )

    def first_call_contained(self, role: str, content: str) -> bool:
        return self.call_contained(0, role, content)

    def call_contained(self, call_index: int, role: str, content: str) -> bool:
        if call_index >= len(self.captured_messages):
            return False
        return any(
            m["role"] == role and content in m["content"]
            for m in self.captured_messages[call_index]
        )


class SessionTestResult:
    def __init__(self, event_spy: EventSpy, session_storage):
        self.events = event_spy
        self.saved_messages = getattr(session_storage, "saved", {})

    def assert_event_occured(self, expected_event: AgentEvent, times: int = 1):
        self.events.assert_event_occured(expected_event, times)

    def as_approval_string(self) -> str:
        return (
            f"# Events\n{self.events.get_events_as_string()}\n\n"
            f"# Saved messages:\n{self._format_saved_messages()}"
        )

    def _format_saved_messages(self) -> str:
        if not self.saved_messages:
            return "None"
        sections = []
        for agent_id in sorted(self.saved_messages.keys()):
            sections.append(f"[{agent_id}]\n{self.saved_messages[agent_id]}")
        return "\n\n".join(sections)


class SessionTestBed:
    def __init__(self):
        class DefaultLLM:
            @property
            def model(self) -> str:
                return "default-model"

            async def call_async(self, messages):
                return LLMResponse(content="")

        self._llm = DefaultLLM()
        self._user_inputs = ["\n"]
        self._start_message = "test message"
        self._escape_hits = None
        self._ctrl_c_hits = None
        self._continue_session = False
        self._todo_cleanup = None
        self._session_storage = None
        self._custom_event_subscriptions = []

    def with_llm_responses(self, responses: list[str]) -> "SessionTestBed":
        self._llm = create_llm_stub(responses)
        return self

    def with_failing_llm(self, error_message: str) -> "SessionTestBed":
        class FailingLLM:
            @property
            def model(self) -> str:
                return "failing-model"

            async def call_async(self, messages):
                raise ClaudeClientError(error_message)

        self._llm = FailingLLM()
        return self

    def with_llm(self, llm) -> "SessionTestBed":
        self._llm = llm
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

    def with_session_storage(self, storage) -> "SessionTestBed":
        self._session_storage = storage
        return self

    def continuing_session(self) -> "SessionTestBed":
        self._continue_session = True
        return self

    def on_event(self, event_type, handler) -> "SessionTestBed":
        self._custom_event_subscriptions.append((event_type, handler))
        return self

    async def run(self) -> SessionTestResult:
        event_bus = SimpleEventBus()
        user_input = UserInputStub(inputs=self._user_inputs, escapes=self._escape_hits)
        session_storage = (
            self._session_storage if self._session_storage else SessionStorageStub()
        )
        todo_cleanup = (
            self._todo_cleanup if self._todo_cleanup is not None else _NoOpTodoCleanup()
        )

        event_spy = EventSpy()
        tracked_events = [
            SessionStartedEvent,
            AgentStartedEvent,
            UserPromptRequestedEvent,
            UserPromptedEvent,
            AssistantSaidEvent,
            AssistantRespondedEvent,
            ToolCalledEvent,
            ToolResultEvent,
            SessionClearedEvent,
            SessionInterruptedEvent,
            SessionEndedEvent,
            ErrorEvent,
            ModelChangedEvent,
        ]
        for event_type in tracked_events:
            event_bus.subscribe(event_type, event_spy.record_event)

        for event_type, handler in self._custom_event_subscriptions:
            event_bus.subscribe(event_type, handler)

        tool_library_factory = ToolLibraryFactoryStub(
            self._llm,
            inputs=self._user_inputs,
            escapes=self._escape_hits,
            interrupts=[self._ctrl_c_hits],
            event_bus=event_bus,
        )

        session = Session(
            event_bus=event_bus,
            session_storage=session_storage,
            tool_library_factory=tool_library_factory,
            agent_library=TestAgentLibrary(),
            user_input=user_input,
            todo_cleanup=todo_cleanup,
            llm_provider=StubLLMProvider.for_testing(self._llm),
            project_tree=DummyProjectTree(),
        )

        await session.run_async(
            create_session_args(
                self._continue_session, start_message=self._start_message
            ),
            AgentId("Agent"),
        )

        return SessionTestResult(event_spy, session_storage)


class TestAgentLibrary:
    def __init__(self):
        self._definitions = {
            "agent": AgentDefinition(
                AgentType("agent"),
                """---
name: Agent
---""",
                GroundRulesStub("Test system prompt"),
            ),
            "coding": AgentDefinition(
                AgentType("coding"),
                """---
name: Coding
---""",
                GroundRulesStub("Test system prompt"),
            ),
            "orchestrator": AgentDefinition(
                AgentType("orchestrator"),
                """---
name: Orchestrator
---""",
                GroundRulesStub("Test system prompt"),
            ),
        }

    def list_agent_types(self) -> list[str]:
        return list(self._definitions.keys())

    def read_agent_definition(self, agent_type: AgentType) -> AgentDefinition:
        return self._definitions[agent_type.raw]

    def starting_agent_id(self) -> AgentId:
        return AgentId(self._starting_agent_definition().agent_name())

    def _starting_agent_definition(self) -> AgentDefinition:
        return self._definitions["agent"]


class _NoOpTodoCleanup:
    def cleanup_all_todos(self) -> None:
        return None

    def cleanup_todos_for_agent(self, agent_id: AgentId) -> None:
        return None
