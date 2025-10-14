#!/usr/bin/env -S uv run --script

import argparse

from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.display_type import DisplayType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import (
    AssistantSaidEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.application.input import Input
from simple_agent.application.session import run_session, SessionArgs
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.claude.claude_config import load_claude_config
from simple_agent.infrastructure.console.console_display import ConsoleDisplay
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.console.console_subagent_display import ConsoleSubagentDisplay
from simple_agent.infrastructure.display_event_handler import DisplayEventHandler
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.infrastructure.textual.textual_display import TextualDisplay
from simple_agent.infrastructure.textual.textual_subagent_display import TextualSubagentDisplay
from simple_agent.infrastructure.textual.textual_user_input import TextualUserInput
from simple_agent.system_prompt_generator import generate_system_prompt


def main():
    args = parse_args()

    if args.show_system_prompt:
        from simple_agent.tools.all_tools import AllTools
        from simple_agent.application.user_input import UserInput

        class DummyUserInput(UserInput):
            def read(self) -> str:
                return ""
            def escape_requested(self) -> bool:
                return False

        create_agent = AgentFactory(
            lambda system_prompt, messages: '',
            SimpleEventBus(),
            lambda agent_id, indent: None,
            lambda indent: Input(DummyUserInput())
        )
        tool_library = AllTools(create_agent=create_agent)
        system_prompt = generate_system_prompt('default.agent.md', tool_library)
        print(system_prompt)
        return

    agent_id = "Agent"
    indent_level = 0
    io = StdIO()

    event_bus = SimpleEventBus()

    if args.display_type == DisplayType.TEXTUAL:
        textual_user_input = TextualUserInput()
        display = TextualDisplay(agent_id, textual_user_input)
        user_input = Input(textual_user_input)
        create_subagent_input = lambda indent: user_input
        display_event_handler = DisplayEventHandler(display)

        def create_subagent_display(_agent_id, _):
            subagent_display = TextualSubagentDisplay(display.app, _agent_id, display_event_handler)
            display_event_handler.register_display(_agent_id, subagent_display)
            return subagent_display
    else:
        display = ConsoleDisplay(indent_level, agent_id, io)
        console_user_input = ConsoleUserInput(indent_level, display.io)
        user_input = Input(console_user_input)
        create_subagent_input = lambda indent: Input(ConsoleUserInput(indent, io))
        display_event_handler = DisplayEventHandler(display)

        def create_subagent_display(_agent_id, indent):
            subagent_display = ConsoleSubagentDisplay(indent, _agent_id, io, display_event_handler)
            display_event_handler.register_display(_agent_id, subagent_display)
            return subagent_display

    if args.start_message:
        user_input.stack(args.start_message)
    session_storage = JsonFileSessionStorage()

    if args.stub_llm:
        llm = create_llm_stub()
    else:
        claude_config = load_claude_config()
        llm = ClaudeLLM(claude_config)

    system_prompt_generator = lambda tool_library: generate_system_prompt('default.agent.md', tool_library)

    event_bus.subscribe(SessionStartedEvent, display_event_handler.handle_session_started)
    event_bus.subscribe(UserPromptRequestedEvent, display_event_handler.handle_user_prompt_requested)
    event_bus.subscribe(UserPromptedEvent, display_event_handler.handle_user_prompted)
    event_bus.subscribe(AssistantSaidEvent, display_event_handler.handle_assistant_said)
    event_bus.subscribe(ToolCalledEvent, display_event_handler.handle_tool_called)
    event_bus.subscribe(ToolResultEvent, display_event_handler.handle_tool_result)
    event_bus.subscribe(SessionInterruptedEvent, display_event_handler.handle_session_interrupted)
    event_bus.subscribe(SessionEndedEvent, display_event_handler.handle_session_ended)

    from simple_agent.tools.all_tools import AllTools

    create_agent = AgentFactory(
        llm,
        event_bus,
        create_subagent_display,
        create_subagent_input
    )

    tools = AllTools(
        llm,
        indent_level,
        agent_id,
        event_bus,
        user_input,
        create_subagent_display,
        create_subagent_input,
        create_agent
    )

    run_session(
        args.continue_session,
        agent_id,
        system_prompt_generator,
        user_input,
        llm,
        tools,
        session_storage,
        event_bus
    )

    display.exit()


def parse_args(argv=None) -> SessionArgs:
    parser = argparse.ArgumentParser(description="Simple Agent")
    parser.add_argument("-c", "--continue", action="store_true", help="Continue previous session")
    parser.add_argument(
        "-s", "--system-prompt", action="store_true",
        help="Print the current system prompt including AGENTS.md content"
    )
    parser.add_argument(
        "-ui", "--user-interface", choices=["textual", "console"], default="textual",
        help="Choose the user interface (default: textual)"
    )
    parser.add_argument("--stub", action="store_true", help="Use LLM stub for testing")
    parser.add_argument("message", nargs="*", help="Message to send to Claude")
    parsed = parser.parse_args(argv)
    display_type = DisplayType(getattr(parsed, "user_interface"))
    return SessionArgs(
        bool(getattr(parsed, "continue")),
        build_start_message(parsed.message),
        bool(getattr(parsed, "system_prompt")),
        display_type,
        bool(getattr(parsed, "stub")
    ))


def build_start_message(message_parts):
    if not message_parts:
        return None
    return " ".join(message_parts)


def create_llm_stub():
    responses = [
        "Starting task\n🛠️ subagent default Run bash echo hello world and then complete",
        "🛠️ subagent default Run bash echo hello world and then complete",
        "🛠️ bash echo hello world",
        "🛠️ complete-task Task completed successfully",
        "🛠️ complete-task Task completed successfully",
        "🛠️ complete-task Main task completed successfully"
    ]
    call_count = 0

    def llm_stub(system_prompt, messages):
        nonlocal call_count
        response = responses[call_count] if call_count < len(responses) else responses[-1]
        call_count += 1
        return response

    return llm_stub


if __name__ == "__main__":
    main()
