#!/usr/bin/env -S uv run --script

import argparse
import os

from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.agent_id import AgentId
from simple_agent.application.app_context import AppContext
from simple_agent.application.display_type import DisplayType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.input import Input
from simple_agent.application.session import SessionArgs, run_session
from simple_agent.application.session_storage import NoOpSessionStorage
from simple_agent.application.subagent_context import SubagentContext
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.application.user_input import DummyUserInput
from simple_agent.infrastructure.agent_library import create_agent_library, extract_agents_path_from_config
from simple_agent.tools.all_tools import AllToolsFactory
from simple_agent.infrastructure.configuration import get_starting_agent, load_user_configuration
from simple_agent.infrastructure.event_logger import EventLogger
from simple_agent.infrastructure.subscribe_events import subscribe_events
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage
from simple_agent.infrastructure.llm import create_llm
from simple_agent.infrastructure.non_interactive_user_input import NonInteractiveUserInput
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_display import TextualDisplay
from simple_agent.infrastructure.textual.textual_user_input import TextualUserInput


def main():
    args = parse_args()
    cwd = os.getcwd()
    user_config = load_user_configuration(cwd)

    if args.show_system_prompt:
        return print_system_prompt_command(user_config, cwd, args)

    if args.non_interactive:
        textual_user_input = NonInteractiveUserInput()
    else:
        textual_user_input = TextualUserInput()


    agents_path = None if args.stub_llm else extract_agents_path_from_config(user_config)
    agent_library = create_agent_library(agents_path, cwd)
    starting_agent_type = get_starting_agent(user_config, args)
    agent_definition = agent_library.read_agent_definition(starting_agent_type)
    root_agent_id = AgentId("Agent")
    textual_app = TextualApp.create_and_start(
        textual_user_input,
        root_agent_id=root_agent_id,
        root_agent_title=agent_definition.agent_name()
    )

    display = TextualDisplay(textual_app)
    display.create_agent_tab(root_agent_id, agent_definition.agent_name())

    user_input = Input(textual_user_input)
    if args.start_message:
        user_input.stack(args.start_message)

    session_storage = JsonFileSessionStorage(os.path.join(cwd, "claude-session.json"))
    todo_cleanup = FileSystemTodoCleanup()

    event_logger = EventLogger('.simple-agent.events.log')

    event_bus = SimpleEventBus()
    subscribe_events(event_bus, event_logger, todo_cleanup, display)

    tool_library_factory = AllToolsFactory()

    create_subagent_input = lambda: Input(textual_user_input)

    llm = create_llm(args.stub_llm, user_config)

    app_context = AppContext(
        llm=llm,
        event_bus=event_bus,
        session_storage=session_storage,
        tool_library_factory=tool_library_factory,
        agent_library=agent_library,
        create_subagent_input=create_subagent_input,
    )

    create_agent = AgentFactory(app_context)

    subagent_context = SubagentContext(
        create_agent,
        create_subagent_input,
        0,
        root_agent_id,
        event_bus
    )
    run_session(
        args,
        app_context,
        root_agent_id,
        todo_cleanup,
        user_input,
        agent_definition,
        subagent_context
    )

    textual_app.shutdown()

    return None


def print_system_prompt_command(user_config, cwd, args):
    from simple_agent.application.agent_id import AgentId

    starting_agent_type = get_starting_agent(user_config, args)
    tool_library_factory = AllToolsFactory()
    dummy_event_bus = SimpleEventBus()
    agents_path = extract_agents_path_from_config(user_config)
    agent_library = create_agent_library(agents_path, cwd)
    create_subagent_input = lambda: Input(DummyUserInput())
    app_context = AppContext(
        llm=lambda messages: '',
        event_bus=dummy_event_bus,
        session_storage=NoOpSessionStorage(),
        tool_library_factory=tool_library_factory,
        agent_library=agent_library,
        create_subagent_input=create_subagent_input,
    )
    create_agent = AgentFactory(app_context)
    prompt = agent_library.read_agent_definition(starting_agent_type).load_prompt()
    subagent_context = SubagentContext(
        create_agent,
        create_subagent_input,
        0,
        AgentId("Agent"),
        dummy_event_bus
    )
    tool_library = tool_library_factory.create(prompt.tool_keys, subagent_context)
    tools_documentation = generate_tools_documentation(tool_library.tools, agent_library.list_agent_types())
    system_prompt = prompt.render(tools_documentation)
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
    )


def build_start_message(message_parts):
    if not message_parts:
        return None
    return " ".join(message_parts)


if __name__ == "__main__":
    main()
