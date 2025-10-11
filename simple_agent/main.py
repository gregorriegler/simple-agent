#!/usr/bin/env -S uv run --script

import argparse

from simple_agent.application.input import Input
from simple_agent.application.session import run_session, SessionArgs
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import EventType
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.claude.claude_config import load_claude_config
from simple_agent.application.display_type import DisplayType
from simple_agent.infrastructure.console_display import ConsoleDisplay
from simple_agent.infrastructure.textual_display import TextualDisplay
from simple_agent.infrastructure.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage
from simple_agent.infrastructure.display_event_handler import DisplayEventHandler
from simple_agent.system_prompt_generator import generate_system_prompt


def main():
    args = parse_args()

    if args.show_system_prompt:
        from simple_agent.tools.tool_library import AllTools
        tool_library = AllTools()
        system_prompt = generate_system_prompt(tool_library)
        print(system_prompt)
        return

    display = TextualDisplay() if args.display_type == DisplayType.TEXTUAL else ConsoleDisplay()
    user_input = ConsoleUserInput(display.indent_level, display.io)
    _input = Input(user_input)
    if args.start_message:
        _input.stack(args.start_message)
    session_storage = JsonFileSessionStorage()
    claude_config = load_claude_config()
    llm = ClaudeLLM(claude_config)
    system_prompt_generator = lambda tool_library: generate_system_prompt(tool_library)

    event_bus = SimpleEventBus()
    display_event_handler = DisplayEventHandler(display)

    event_bus.subscribe(EventType.SESSION_STARTED, display_event_handler.handle_session_started)
    event_bus.subscribe(EventType.ASSISTANT_SAID, display_event_handler.handle_assistant_said)
    event_bus.subscribe(EventType.TOOL_RESULT, display_event_handler.handle_tool_result)
    event_bus.subscribe(EventType.SESSION_ENDED, display_event_handler.handle_session_ended)

    run_session(
        args.continue_session,
        _input,
        session_storage,
        llm,
        system_prompt_generator,
        event_bus,
        display_event_handler
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Simple Agent")
    parser.add_argument("-c", "--continue", action="store_true", help="Continue previous session")
    parser.add_argument("-s", "--system-prompt", action="store_true",
                        help="Print the current system prompt including AGENTS.md content")
    parser.add_argument("-ui", "--user-interface", choices=["textual", "console"], default="textual",
                        help="Choose the user interface (default: textual)")
    parser.add_argument("message", nargs="*", help="Message to send to Claude")
    parsed = parser.parse_args(argv)
    display_type = DisplayType(getattr(parsed, "user_interface"))
    return SessionArgs(bool(getattr(parsed, "continue")), build_start_message(parsed.message),
                       bool(getattr(parsed, "system_prompt")), display_type)


def build_start_message(message_parts):
    if not message_parts:
        return None
    return " ".join(message_parts)


if __name__ == "__main__":
    main()
