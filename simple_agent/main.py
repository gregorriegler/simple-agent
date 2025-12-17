#!/usr/bin/env -S uv run --script

import argparse
import os

from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.display_type import DisplayType
from simple_agent.application.emoji_bracket_tool_syntax import EmojiBracketToolSyntax
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import UserPromptRequestedEvent
from simple_agent.application.llm_stub import StubLLMProvider
from simple_agent.application.session import Session, SessionArgs
from simple_agent.application.session_storage import NoOpSessionStorage
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.application.user_input import DummyUserInput
from simple_agent.infrastructure.agent_library import create_agent_library
from simple_agent.infrastructure.configuration import get_starting_agent, load_user_configuration, stub_user_config
from simple_agent.infrastructure.event_logger import EventLogger
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage
from simple_agent.infrastructure.llm import RemoteLLMProvider
from simple_agent.infrastructure.non_interactive_user_input import NonInteractiveUserInput
from simple_agent.infrastructure.subscribe_events import subscribe_events
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_display import TextualDisplay
from simple_agent.infrastructure.textual.textual_user_input import TextualUserInput
from simple_agent.tools.all_tools import AllToolsFactory
from simple_agent.logging_config import setup_logging


def main(on_user_prompt_requested=None):
    setup_logging()

    args = parse_args()
    if on_user_prompt_requested:
        args.on_user_prompt_requested = on_user_prompt_requested
    cwd = os.getcwd()
    if args.stub_llm:
        user_config = stub_user_config()
    else:
        user_config = load_user_configuration(cwd)

    if args.show_system_prompt:
        return print_system_prompt_command(user_config, cwd, args)

    if args.non_interactive:
        textual_user_input = NonInteractiveUserInput()
    else:
        textual_user_input = TextualUserInput()

    agents_path = None if args.stub_llm else user_config.agents_path()
    agent_library = create_agent_library(agents_path, cwd)
    starting_agent_type = get_starting_agent(user_config, args)
    agent_definition = agent_library.read_agent_definition(starting_agent_type)
    root_agent_id = AgentId(agent_definition.agent_name())

    todo_cleanup = FileSystemTodoCleanup()

    if not args.continue_session:
        todo_cleanup.cleanup_all_todos()

    textual_app = TextualApp(textual_user_input, root_agent_id)
    display = TextualDisplay(textual_app)

    session_storage = JsonFileSessionStorage(os.path.join(cwd, "claude-session.json"))

    event_logger = EventLogger()

    event_bus = SimpleEventBus()
    subscribe_events(event_bus, event_logger, todo_cleanup, display)

    if args.on_user_prompt_requested:
        def on_prompt_wrapper(_):
            args.on_user_prompt_requested(textual_app)
        event_bus.subscribe(UserPromptRequestedEvent, on_prompt_wrapper)

    tool_syntax = EmojiBracketToolSyntax()
    tool_library_factory = AllToolsFactory(tool_syntax)

    if args.stub_llm:
        llm_provider = StubLLMProvider()
    else:
        llm_provider = RemoteLLMProvider(user_config)

    session = Session(
        event_bus=event_bus,
        session_storage=session_storage,
        tool_library_factory=tool_library_factory,
        agent_library=agent_library,
        user_input=textual_user_input,
        todo_cleanup=todo_cleanup,
        llm_provider=llm_provider
    )

    if args.test_mode:
        # Test mode: use threaded approach for compatibility with test harness
        textual_app = TextualApp.create_and_start_test(textual_user_input, root_agent_id)
        display = TextualDisplay(textual_app)
        subscribe_events(event_bus, event_logger, todo_cleanup, display)
        session.run(args, root_agent_id, agent_definition)
        return textual_app

    # Normal mode: Textual owns the event loop, session runs as a task
    async def run_session():
        await session.run_async(args, root_agent_id, agent_definition)

    textual_app.run_with_session(run_session)
    return None


def print_system_prompt_command(user_config, cwd, args):
    from simple_agent.application.tool_library_factory import ToolContext

    starting_agent_type = get_starting_agent(user_config, args)
    tool_syntax = EmojiBracketToolSyntax()
    tool_library_factory = AllToolsFactory(tool_syntax)
    dummy_event_bus = SimpleEventBus()
    agents_path = user_config.agents_path()
    agent_library = create_agent_library(agents_path, cwd)
    session_storage = NoOpSessionStorage()
    agent_factory = AgentFactory(
        dummy_event_bus,
        session_storage,
        tool_library_factory,
        agent_library,
        DummyUserInput(),
        StubLLMProvider.dummy()
    )
    agent_definition = agent_library.read_agent_definition(starting_agent_type)
    agent_id = AgentId("Agent")
    tool_context = ToolContext(
        agent_definition.tool_keys(),
        agent_id
    )
    spawner = agent_factory.create_spawner(agent_id)
    tool_library = tool_library_factory.create(tool_context, spawner, AgentTypes(agent_library.list_agent_types()))
    tools_documentation = generate_tools_documentation(tool_library.tools, tool_syntax)
    system_prompt = agent_definition.prompt().render(tools_documentation)
    print(system_prompt)
    return


def parse_args(argv=None) -> SessionArgs:
    parser = argparse.ArgumentParser(description="Simple Agent")
    parser.add_argument("-a", "--agent", action='store', type=str, help="Defines the starting agent")
    parser.add_argument("-c", "--continue", action="store_true", help="Continue previous session")
    parser.add_argument(
        "-s", "--system-prompt", action="store_true",
        help="Print the current system prompt including AGENTS.md content"
    )
    parser.add_argument(
        "-ni", "--non-interactive", action="store_true",
        help="Run in non-interactive mode (no user input prompts)"
    )
    parser.add_argument("--stub", action="store_true", help="Use LLM stub for testing")
    parser.add_argument("--test", action="store_true", help="Run in test mode using Textual's run_test()")
    parser.add_argument("message", nargs="*", help="Message to send to the agent")
    parsed = parser.parse_args(argv)
    return SessionArgs(
        bool(getattr(parsed, "continue")),
        build_start_message(parsed.message),
        bool(getattr(parsed, "system_prompt")),
        DisplayType.TEXTUAL,
        bool(getattr(parsed, "stub")),
        bool(getattr(parsed, "non_interactive")),
        getattr(parsed, "agent"),
        bool(getattr(parsed, "test")),
    )


def build_start_message(message_parts):
    if not message_parts:
        return None
    return " ".join(message_parts)


if __name__ == "__main__":
    main()
