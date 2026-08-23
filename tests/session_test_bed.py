import asyncio

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_task_manager import AgentTaskManager
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.event_store import EventStore, NoOpEventStore
from simple_agent.application.events import (
    AgentEvent,
    AgentFinishedEvent,
    AgentStartedEvent,
    AssistantRespondedEvent,
    AssistantSaidEvent,
    CheckpointReachedEvent,
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
from simple_agent.application.events_to_messages import events_to_messages
from simple_agent.application.llm import ChatMessages, LLMResponse, TokenUsage
from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.application.observer_definition import ObserverDefinition
from simple_agent.application.session import Session
from simple_agent.application.text_response import emoji_response
from simple_agent.infrastructure.claude.claude_client import ClaudeClientError
from simple_agent.infrastructure.file_intent import FileIntent
from tests.event_spy import EventSpy
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
        return emoji_response(content, self.model, TokenUsage(0, 0, 0))

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
    def __init__(self, event_spy: EventSpy):
        self.events = event_spy

    def current_messages(self, agent_id: AgentId) -> str:
        messages = events_to_messages(self.events.get_all_events(), agent_id)
        return "\n".join(f"{msg['role']}: {msg['content']}" for msg in messages)

    def all_messages(self) -> str:
        result = ""
        current_agent = ""
        for event in self.events.get_all_events():
            if isinstance(event, UserPromptedEvent):
                if current_agent != event.agent_id:
                    current_agent = event.agent_id
                    result += "[" + str(current_agent) + "]\n"
                result += "user: " + event.input_text + "\n"
            elif isinstance(event, ToolResultEvent):
                result += "user: " + str(event.result) + "\n"
            elif isinstance(event, AssistantRespondedEvent):
                result += "assistant: " + event.response + "\n"

        return result

    def assert_event_occured(self, expected_event: AgentEvent, times: int = 1):
        self.events.assert_event_occured(expected_event, times)

    def as_approval_string(self) -> str:
        return (
            f"# Events\n{self.events.get_events_as_string()}\n\n"
            f"# Messages:\n{self.all_messages()}\n"
        )


class SessionTestBed:
    def __init__(self):
        class DefaultLLM:
            @property
            def model(self) -> str:
                return "default-model"

            async def call_async(self, messages):
                return LLMResponse(answer="")

        self._llm = DefaultLLM()
        self._user_inputs = ["\n"]
        self._start_message = "test message"
        self._escape_hits = None
        self._typed_while_working = None
        self._ctrl_c_hits = None
        self._continue_session = False
        self._event_store: EventStore | None = None
        self._custom_event_subscriptions = []
        self._observers: list[str] = []
        self._diffs = ["a production diff"]
        self._observer_llm = create_llm_stub([], default="🛠️[complete-task nothing /]")

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

    def with_messages_typed_while_working(
        self, messages: list[str]
    ) -> "SessionTestBed":
        self._typed_while_working = messages
        return self

    def with_escape_hits(self, hits: list[bool]) -> "SessionTestBed":
        self._escape_hits = hits
        return self

    def with_ctrl_c_hits(self, hits: list[bool]) -> "SessionTestBed":
        self._ctrl_c_hits = hits
        return self

    def with_event_store(self, event_store: EventStore) -> "SessionTestBed":
        self._event_store = event_store
        return self

    def observed_by(self, observers: list[str], *diffs: str) -> "SessionTestBed":
        self._observers = observers
        self._diffs = list(diffs) or self._diffs
        return self

    def with_observer_responses(self, responses: list[str]) -> "SessionTestBed":
        self._observer_llm = create_llm_stub(responses)
        return self

    def continuing_session(self) -> "SessionTestBed":
        self._continue_session = True
        return self

    def on_event(self, event_type, handler) -> "SessionTestBed":
        self._custom_event_subscriptions.append((event_type, handler))
        return self

    async def run(self) -> SessionTestResult:
        event_bus = SimpleEventBus()
        user_input = UserInputStub(
            inputs=self._user_inputs,
            escapes=self._escape_hits,
            typed_while_working=self._typed_while_working,
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
            CheckpointReachedEvent,
            AgentFinishedEvent,
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

        if self._event_store:
            event_bus.subscribe(UserPromptedEvent, self._event_store.persist)
            event_bus.subscribe(AssistantRespondedEvent, self._event_store.persist)
            event_bus.subscribe(AgentStartedEvent, self._event_store.persist)
            event_bus.subscribe(AgentFinishedEvent, self._event_store.persist)
            event_bus.subscribe(ToolResultEvent, self._event_store.persist)
            event_bus.subscribe(SessionClearedEvent, self._event_store.persist)
            event_bus.subscribe(ModelChangedEvent, self._event_store.persist)

        agent_library = TestAgentLibrary(self._observers)

        tool_library_factory = ToolLibraryFactoryStub(
            self._llm,
            inputs=self._user_inputs,
            escapes=self._escape_hits,
            interrupts=[self._ctrl_c_hits],
            event_bus=event_bus,
            agent_library=agent_library,
        )

        root_agent_id = AgentId("Agent")
        agent_task_manager = AgentTaskManager()
        event_store = self._event_store or NoOpEventStore()
        session = Session(
            root_agent_id,
            event_bus=event_bus,
            tool_library_factory=tool_library_factory,
            agent_library=agent_library,
            user_input=user_input,
            llm_provider=TestLLMProvider(self._llm, self._observer_llm),
            project_tree=DummyProjectTree(),
            event_store=event_store,
            agent_task_manager=agent_task_manager,
            observer_library=TestObserverLibrary(),
            change_reporter=ChangeReporterStub(self._diffs),
            intent=FileIntent(root_agent_id),
        )

        asyncio.create_task(
            session.run_async(
                create_session_args(
                    self._continue_session, start_message=self._start_message
                )
            )
        )

        while True:
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if not tasks:
                break
            await asyncio.gather(*tasks)

        return SessionTestResult(event_spy)


class ChangeReporterStub:
    def __init__(self, diffs: list[str]):
        self._diffs = list(diffs)

    def diff(self) -> str:
        if len(self._diffs) > 1:
            return self._diffs.pop(0)
        return self._diffs[0]


OBSERVER_MODEL = "observer-model"


class TestLLMProvider:
    def __init__(self, agent_llm, observer_llm):
        self._agent_llm = agent_llm
        self._observer_llm = observer_llm

    def get(self, model_name: str | None = None, tools: list | None = None):
        if model_name == OBSERVER_MODEL:
            return self._observer_llm
        return self._agent_llm

    def get_available_models(self) -> list[str]:
        return [self._agent_llm.model]

    def tool_syntax(self, model_name: str | None = None) -> str:
        return "emoji"


class TestObserverLibrary:
    def read_observer_definition(self, name: str) -> ObserverDefinition:
        return ObserverDefinition(
            AgentType(name),
            f"---\n"
            f"name: {name.capitalize()}\n"
            f"tools: [cat]\n"
            f"model: {OBSERVER_MODEL}\n"
            f"---\n"
            f"Watch the {name}.",
            GroundRulesStub("Test system prompt"),
        )


class TestAgentLibrary:
    def __init__(self, observers: list[str] | None = None):
        self._definitions = {
            "agent": AgentDefinition(
                AgentType("agent"),
                f"""---
name: Agent
observers: {observers or []}
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
