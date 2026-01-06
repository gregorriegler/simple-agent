#!/usr/bin/env -S uv run --script

import argparse
import asyncio
import io
import os
import sys
from pathlib import Path
from typing import Protocol

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
from simple_agent.infrastructure.event_logger import EventLogger
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage
from simple_agent.infrastructure.llm import RemoteLLMProvider
from simple_agent.infrastructure.non_interactive_user_input import (
    NonInteractiveUserInput,
)
from simple_agent.infrastructure.project_tree import FileSystemProjectTree
from simple_agent.infrastructure.subscribe_events import subscribe_events
from simple_agent.infrastructure.textual.textual_app import TextualApp
from simple_agent.infrastructure.textual.textual_user_input import TextualUserInput
from simple_agent.infrastructure.user_configuration import (
    UserConfiguration,
    ConfigurationError,
)
from simple_agent.logging_config import setup_logging
from simple_agent.tools.all_tools import AllToolsFactory


class TextualRunStrategy(Protocol):
    allow_async: bool

    async def run(self, textual_app: TextualApp, run_session): ...


class ProductionTextualRunStrategy(TextualRunStrategy):
    allow_async = False

    async def run(self, textual_app: TextualApp, run_session):
        await textual_app.run_with_session_async(run_session)
        return None


class TestTextualRunStrategy(TextualRunStrategy):
    allow_async = True

    async def run(self, textual_app: TextualApp, run_session):
        async with textual_app.run_test() as pilot:
            if sys.platform == "win32":
                textual_app._original_stdout = io.StringIO()
                textual_app._original_stderr = io.StringIO()
            textual_app._pilot = pilot
            await pilot.pause()  # Wait for app to fully mount
            session_task = asyncio.create_task(run_session())
            await session_task

        return textual_app


async def _run_main(run_strategy: TextualRunStrategy, event_subscriber=None):
    args = parse_args()
    cwd = os.getcwd()
    user_config = UserConfiguration.create_from_args(args, cwd)
    setup_logging(user_config=user_config)

    if args.show_system_prompt:
        return print_system_prompt_command(user_config, cwd, args)

    if args.non_interactive:
        textual_user_input = NonInteractiveUserInput()
    else:
        textual_user_input = TextualUserInput()

    agent_library = create_agent_library(user_config, args)

    todo_cleanup = FileSystemTodoCleanup()

    if not args.continue_session:
        todo_cleanup.cleanup_all_todos()

    session_storage = JsonFileSessionStorage(os.path.join(cwd, "claude-session.json"))

    event_logger = EventLogger()
    event_bus = SimpleEventBus()

    tool_syntax = EmojiBracketToolSyntax()
    tool_library_factory = AllToolsFactory(tool_syntax)

    if args.stub_llm:
        llm_provider = StubLLMProvider()
    else:
        llm_provider = RemoteLLMProvider(user_config)

    project_tree = FileSystemProjectTree(Path(cwd))

    session = Session(
        event_bus=event_bus,
        session_storage=session_storage,
        tool_library_factory=tool_library_factory,
        agent_library=agent_library,
        user_input=textual_user_input,
        todo_cleanup=todo_cleanup,
        llm_provider=llm_provider,
        project_tree=project_tree,
    )

    starting_agent_id = agent_library.starting_agent_id().with_root(Path(cwd))
    textual_app = TextualApp(
        textual_user_input,
        starting_agent_id,
        available_models=llm_provider.get_available_models(),
    )
    subscribe_events(event_bus, event_logger, todo_cleanup, textual_app)
    if event_subscriber:
        event_subscriber(event_bus, textual_app)

    async def run_session():
        await session.run_async(args, starting_agent_id)

    return await run_strategy.run(textual_app, run_session)


def main():
    try:
        return asyncio.run(_run_main(ProductionTextualRunStrategy()))
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)


async def main_async(on_user_prompt_requested=None):
    def subscribe_prompt(event_bus, textual_app):
        if not on_user_prompt_requested:
            return

        def on_prompt_wrapper(_):
            result = on_user_prompt_requested(textual_app)
            asyncio.create_task(result)

        event_bus.subscribe(UserPromptRequestedEvent, on_prompt_wrapper)

    return await _run_main(TestTextualRunStrategy(), subscribe_prompt)


def print_system_prompt_command(user_config, cwd, args):
    from simple_agent.application.tool_library_factory import ToolContext

    tool_syntax = EmojiBracketToolSyntax()
    tool_library_factory = AllToolsFactory(tool_syntax)
    dummy_event_bus = SimpleEventBus()
    agent_library = create_agent_library(user_config, args)
    session_storage = NoOpSessionStorage()
    agent_factory = AgentFactory(
        dummy_event_bus,
        session_storage,
        tool_library_factory,
        agent_library,
        DummyUserInput(),
        StubLLMProvider.dummy(),
        FileSystemProjectTree(Path(cwd)),
    )
    agent_definition = agent_library._starting_agent_definition()
    agent_id = AgentId("Agent", root=Path(cwd))
    tool_context = ToolContext(agent_definition.tool_keys(), agent_id)
    spawner = agent_factory.create_spawner(agent_id)
    tool_library = tool_library_factory.create(
        tool_context, spawner, AgentTypes(agent_library.list_agent_types())
    )
    tools_documentation = generate_tools_documentation(tool_library.tools, tool_syntax)
    system_prompt = agent_definition.prompt().render(
        tools_documentation, FileSystemProjectTree(Path(cwd))
    )
    print(system_prompt)
    return


def parse_args(argv=None) -> SessionArgs:
    parser = argparse.ArgumentParser(description="Simple Agent")
    parser.add_argument(
        "-a", "--agent", action="store", type=str, help="Defines the starting agent"
    )
    parser.add_argument(
        "-c", "--continue", action="store_true", help="Continue previous session"
    )
    parser.add_argument(
        "-s",
        "--system-prompt",
        action="store_true",
        help="Print the current system prompt including AGENTS.md content",
    )
    parser.add_argument(
        "-ni",
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (no user input prompts)",
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
