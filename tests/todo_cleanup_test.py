from pathlib import Path

from approvaltests import verify, Options

from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.input import Input
from simple_agent.application.session import run_session
from simple_agent.infrastructure.console.console_display import ConsoleDisplay
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.display_event_handler import DisplayEventHandler
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from .print_spy import IOSpy
from .test_helpers import all_scrubbers
from .test_session_storage import SessionStorageStub
from .test_tool_library import ToolLibraryStub


def test_new_session_deletes_all_todo_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    todo_files = [
        ".Agent.todos.md",
        ".Agent.Coding.todos.md",
        ".Agent.Orchestrator.todos.md",
        ".some.other.todos.md"
    ]
    for filename in todo_files:
        Path(filename).write_text(f"content of {filename}")

    other_files = [
        "normal.md",
        ".gitignore",
        "test.txt"
    ]
    for filename in other_files:
        Path(filename).write_text(f"content of {filename}")

    run_test_session(continue_session=False)

    remaining_files = sorted([f.name for f in Path.cwd().iterdir() if f.is_file()])

    result = f"Remaining files after new session:\n" + "\n".join(remaining_files)
    verify(result, options=Options().with_scrubber(all_scrubbers()))


def test_continued_session_keeps_todo_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    todo_files = [
        ".Agent.todos.md",
        ".Agent.Coding.todos.md"
    ]
    for filename in todo_files:
        Path(filename).write_text(f"content of {filename}")

    run_test_session(continue_session=True)

    remaining_files = sorted([f.name for f in Path.cwd().iterdir() if f.is_file()])

    result = f"Remaining files after continued session:\n" + "\n".join(remaining_files)
    verify(result, options=Options().with_scrubber(all_scrubbers()))


def run_test_session(continue_session):
    def llm_stub(system_prompt, messages):
        return ""

    io_spy = IOSpy(["\n"])
    display = ConsoleDisplay(0, "Agent", io_spy)
    user_input_port = ConsoleUserInput(display.indent_level, io=io_spy)
    user_input = Input(user_input_port)
    user_input.stack("test message")

    event_bus = SimpleEventBus()
    display_handler = DisplayEventHandler(display)

    test_tool_library = ToolLibraryStub(
        llm_stub,
        io=io_spy,
        interrupts=[None],
        event_bus=event_bus,
        display_event_handler=display_handler
    )

    test_session_storage = SessionStorageStub()
    todo_cleanup = FileSystemTodoCleanup()

    run_session(
        continue_session,
        "Agent",
        "Test system prompt",
        user_input,
        llm_stub,
        test_tool_library,
        test_session_storage,
        event_bus,
        todo_cleanup
    )
