from approvaltests import verify

from simple_agent.application.input import Input
from simple_agent.application.session import run_session
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AssistantRespondedEvent,
    AssistantSaidEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.infrastructure.console.console_display import ConsoleDisplay
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.display_event_handler import DisplayEventHandler
from .event_spy import EventSpy
from .print_spy import IOSpy
from .test_session_storage import SessionStorageStub
from .test_tool_library import ToolLibraryStub


def test_subagent():
    verify_chat(
        ["Create a subagent that says hello", "\n"], [
            "🛠️ subagent coding say hello",
            "hello\n🛠️ complete-task I successfully said hello"
        ]
    )


def test_nested_agent_test():
    verify_chat(
        ["Create a subagent that creates another subagent", "\n"], [
            "🛠️ subagent orchestrator create another subagent",
            "🛠️ subagent coding say nested hello",
            "nested hello\n🛠️ complete-task I successfully said nested hello",
            "🛠️ complete-task I successfully created another subagent",
            "🛠️ complete-task I successfully created a subagent"
        ]
    )


def test_agent_says_after_subagent():
    verify_chat(
        ["Create a subagent that says hello, then say goodbye", "\n"], [
            "🛠️ subagent coding say hello",
            "hello\n🛠️ complete-task I successfully said hello",
            "goodbye"
        ]
    )


def verify_chat(inputs, answers, escape_hits=None, ctrl_c_hits=None):
    llm_stub = create_llm_stub(answers)
    message, *remaining_inputs = inputs
    io_spy = IOSpy(remaining_inputs, escape_hits)
    display = ConsoleDisplay(0, "Agent", io_spy)
    user_input_port = ConsoleUserInput(display.indent_level, io=io_spy)
    user_input = Input(user_input_port)
    user_input.stack(message)
    test_session_storage = SessionStorageStub()
    event_bus = SimpleEventBus()
    display_handler = DisplayEventHandler(display)

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

    event_bus.subscribe(AssistantSaidEvent, display_handler.handle_assistant_said)
    event_bus.subscribe(ToolCalledEvent, display_handler.handle_tool_called)
    event_bus.subscribe(ToolResultEvent, display_handler.handle_tool_result)
    event_bus.subscribe(SessionStartedEvent, display_handler.handle_session_started)
    event_bus.subscribe(SessionInterruptedEvent, display_handler.handle_session_interrupted)
    event_bus.subscribe(SessionEndedEvent, display_handler.handle_session_ended)

    test_tool_library = ToolLibraryStub(
        llm_stub,
        io=io_spy,
        interrupts=[ctrl_c_hits],
        event_bus=event_bus,
        display_event_handler=display_handler
    )

    run_session(
        False,
        "Agent",
        system_prompt_stub,
        user_input,
        llm_stub,
        test_tool_library,
        test_session_storage,
        event_bus
    )

    result = f"# Events\n{event_spy.get_events_as_string()}\n\n# Saved messages:\n{test_session_storage.saved}"
    verify(result)


def create_llm_stub(answer):
    if isinstance(answer, list):
        answer_index = 0

        def llm_stub(system_prompt, messages):
            nonlocal answer_index
            if answer_index < len(answer):
                result = answer[answer_index]
                answer_index += 1
                return result
            if answer:
                return answer[-1]
            return ""

        return llm_stub

    def llm_answer(system_prompt, messages):
        return answer

    return llm_answer


def system_prompt_stub(_):
    return "Test system prompt"
