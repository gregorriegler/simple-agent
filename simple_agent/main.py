#!/usr/bin/env -S uv run --script

import argparse

from simple_agent.application.agent_factory import AgentFactory
from simple_agent.application.display import DummyDisplay
from simple_agent.application.display_type import DisplayType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.infrastructure.all_tools_factory import AllToolsFactory
from simple_agent.application.events import (
    AssistantSaidEvent,
    SessionEndedEvent,
    SessionInterruptedEvent,
    SessionStartedEvent,
    SubagentFinishedEvent,
    ToolCalledEvent,
    ToolResultEvent,
    UserPromptRequestedEvent,
    UserPromptedEvent,
)
from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.application.input import Input
from simple_agent.application.session import run_session, SessionArgs
from simple_agent.application.session_storage import NoOpSessionStorage
from simple_agent.application.user_input import DummyUserInput
from simple_agent.application.subagent_context import SubagentContext

from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.claude.claude_config import load_claude_config
from simple_agent.infrastructure.console.console_display import ConsoleDisplay
from simple_agent.infrastructure.console.console_subagent_display import ConsoleSubagentDisplay
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.display_event_handler import DisplayEventHandler
from simple_agent.infrastructure.event_logger import EventLogger
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from simple_agent.infrastructure.json_file_session_storage import JsonFileSessionStorage
from simple_agent.infrastructure.non_interactive_user_input import NonInteractiveUserInput
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.infrastructure.system_prompt.agent_definition import load_agent_prompt
from simple_agent.infrastructure.textual.textual_display import TextualDisplay
from simple_agent.infrastructure.textual.textual_subagent_display import TextualSubagentDisplay
from simple_agent.infrastructure.textual.textual_user_input import TextualUserInput
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.infrastructure.file_system_agent_type_discovery import FileSystemAgentTypeDiscovery

def main():
    args = parse_args()

    if args.show_system_prompt:
        return print_system_prompt_command()

    agent_id = "Agent"
    indent_level = 0
    io = StdIO()

    event_bus = SimpleEventBus()

    event_logger = EventLogger('.simple-agent.events.log')
    event_bus.subscribe(SessionStartedEvent, event_logger.log_event)
    event_bus.subscribe(UserPromptRequestedEvent, event_logger.log_event)
    event_bus.subscribe(UserPromptedEvent, event_logger.log_event)
    event_bus.subscribe(AssistantSaidEvent, event_logger.log_event)
    event_bus.subscribe(ToolCalledEvent, event_logger.log_event)
    event_bus.subscribe(ToolResultEvent, event_logger.log_event)
    event_bus.subscribe(SessionInterruptedEvent, event_logger.log_event)
    event_bus.subscribe(SessionEndedEvent, event_logger.log_event)

    def handle_subagent_finished(event: SubagentFinishedEvent) -> None:
        todo_cleanup.cleanup_todos_for_agent(event.subagent_id)

    event_bus.subscribe(SubagentFinishedEvent, handle_subagent_finished)

    if args.display_type == DisplayType.TEXTUAL:
        if args.non_interactive:
            textual_user_input = NonInteractiveUserInput()
        else:
            textual_user_input = TextualUserInput()
        display = TextualDisplay(agent_id, textual_user_input)
        user_input = Input(textual_user_input)
        create_subagent_input = lambda indent: user_input
        display_event_handler = DisplayEventHandler(display)

        def _create_textual_subagent_display(_agent_id, _agent_name, _indent):
            subagent_display = TextualSubagentDisplay(display.app, _agent_id, _agent_name, display_event_handler)
            display_event_handler.register_display(_agent_id, subagent_display)
            return subagent_display

        create_subagent_display = _create_textual_subagent_display
    else:
        display = ConsoleDisplay(indent_level, agent_id, io)
        if args.non_interactive:
            console_user_input = NonInteractiveUserInput()
        else:
            console_user_input = ConsoleUserInput(indent_level, display.io)
        user_input = Input(console_user_input)
        create_subagent_input = lambda indent: Input(
            NonInteractiveUserInput() if args.non_interactive else ConsoleUserInput(indent, io)
            )
        display_event_handler = DisplayEventHandler(display)

        def _create_console_subagent_display(_agent_id, _agent_name, _indent):
            subagent_display = ConsoleSubagentDisplay(_indent, _agent_id, _agent_name, io, display_event_handler)
            display_event_handler.register_display(_agent_id, subagent_display)
            return subagent_display

        create_subagent_display = _create_console_subagent_display

    if args.start_message:
        user_input.stack(args.start_message)
    session_storage = JsonFileSessionStorage()
    todo_cleanup = FileSystemTodoCleanup()

    if args.stub_llm:
        llm = create_llm_stub(
            [
                "Starting task\n🛠️ subagent orchestrator Run bash echo hello world and then complete",
                "Subagent1 handling the orchestrator task\n🛠️ subagent coding Run bash echo hello world and then complete",
                "Subagent2 updating todos\n🛠️ write-todos\n- [x] Feature exploration\n- [ ] **Implementing tool**\n- [ ] Initial setup\n🛠️🔚",
                "Subagent2 running the bash command\n🛠️ bash echo hello world",
                "Subagent2 reading AGENTS.md\n🛠️ cat AGENTS.md",
                "🛠️ create-file newfile.txt\ncontent of newfile.txt",
                "🛠️ edit-file newfile.txt replace 1\nnew content of newfile.txt",
                "🛠️ bash rm newfile.txt",
                "Subagent2 completed successfully\n🛠️ complete-task Task completed successfully",
                "Subagent1 coding task completed\n🛠️ complete-task Task completed successfully",
                "All tasks finished\n🛠️ complete-task Main task completed successfully"
            ]
        )
    else:
        claude_config = load_claude_config()
        llm = ClaudeLLM(claude_config)

    event_bus.subscribe(SessionStartedEvent, display_event_handler.handle_session_started)
    event_bus.subscribe(UserPromptRequestedEvent, display_event_handler.handle_user_prompt_requested)
    event_bus.subscribe(UserPromptedEvent, display_event_handler.handle_user_prompted)
    event_bus.subscribe(AssistantSaidEvent, display_event_handler.handle_assistant_said)
    event_bus.subscribe(ToolCalledEvent, display_event_handler.handle_tool_called)
    event_bus.subscribe(ToolResultEvent, display_event_handler.handle_tool_result)
    event_bus.subscribe(SessionInterruptedEvent, display_event_handler.handle_session_interrupted)
    event_bus.subscribe(SessionEndedEvent, display_event_handler.handle_session_ended)

    tool_library_factory = AllToolsFactory()
    agent_type_discovery = FileSystemAgentTypeDiscovery()

    create_agent = AgentFactory(
        llm,
        event_bus,
        create_subagent_display,
        create_subagent_input,
        load_agent_prompt,
        session_storage,
        tool_library_factory,
        agent_type_discovery
    )

    prompt = load_agent_prompt('orchestrator')

    subagent_context = SubagentContext(
        create_agent,
        create_subagent_display,
        create_subagent_input,
        indent_level,
        agent_id,
        event_bus
    )

    tools = tool_library_factory.create(prompt.tool_keys, subagent_context)

    tools_documentation = generate_tools_documentation(tools.tools, agent_type_discovery)
    system_prompt = prompt.render(tools_documentation)

    run_session(
        args.continue_session,
        agent_id,
        system_prompt,
        user_input,
        llm,
        tools,
        session_storage,
        event_bus,
        todo_cleanup,
        prompt.name
    )

    display.exit()
    return None


def print_system_prompt_command():
    tool_library_factory = AllToolsFactory()
    agent_type_discovery = FileSystemAgentTypeDiscovery()
    dummy_event_bus = SimpleEventBus()
    create_agent = AgentFactory(
        lambda system_prompt, messages: '',
        dummy_event_bus,
        lambda agent_id, indent: DummyDisplay(),
        lambda indent: Input(DummyUserInput()),
        load_agent_prompt,
        NoOpSessionStorage(),
        tool_library_factory,
        agent_type_discovery
    )
    prompt = load_agent_prompt('orchestrator')
    subagent_context = SubagentContext(
        create_agent,
        lambda agent_id, indent: DummyDisplay(),
        lambda indent: Input(DummyUserInput()),
        0,
        "Agent",
        dummy_event_bus
    )
    tool_library = tool_library_factory.create(prompt.tool_keys, subagent_context)
    tools_documentation = generate_tools_documentation(tool_library.tools, agent_type_discovery)
    system_prompt = prompt.render(tools_documentation)
    print(system_prompt)
    return


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
    parser.add_argument(
        "-ni", "--non-interactive", action="store_true",
        help="Run in non-interactive mode (no user input prompts)"
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
        bool(getattr(parsed, "stub")),
        bool(getattr(parsed, "non_interactive"))
    )


def build_start_message(message_parts):
    if not message_parts:
        return None
    return " ".join(message_parts)


if __name__ == "__main__":
    main()
