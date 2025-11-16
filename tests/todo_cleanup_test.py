from pathlib import Path

from approvaltests import verify, Options

from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import AgentCreatedEvent, AgentFinishedEvent
from simple_agent.application.input import Input
from simple_agent.application.session import run_session
from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.infrastructure.console.console_display import ConsoleAgentDisplay
from simple_agent.infrastructure.console.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from .fake_display import FakeDisplay
from .print_spy import IOSpy
from .test_helpers import all_scrubbers, create_test_prompt, create_session_args
from .test_session_storage import SessionStorageStub
from .test_tool_library import ToolLibraryStub


def test_new_session_deletes_all_todo_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    files = [
        ".todos.md",
        ".Agent.todos.md",
        ".Agent.Coding.todos.md",
        ".Agent.Orchestrator.todos.md",
        ".some.other.todos.md",
        "normal.md",
        ".gitignore",
        "test.txt"
    ]
    for filename in files:
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


def test_subagent_cleanup_deletes_subagent_todo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    created_files = set()
    original_write_text = Path.write_text

    def capture_write_text(path_obj, data, encoding=None, errors=None, newline=None):
        created_files.add(path_obj.name)
        return original_write_text(path_obj, data, encoding=encoding, errors=errors, newline=newline)

    monkeypatch.setattr(Path, "write_text", capture_write_text)

    llm_stub = create_llm_stub(
        [
            "🛠️ subagent coding handle-task",
            "🛠️ write-todos\n- [ ] Coding task\n🛠️🔚",
            "🛠️ complete-task Subagent finished",
            "🛠️ complete-task Root finished"
        ]
    )

    todo_cleanup = SpyFileSystemTodoCleanup()

    run_test_session(continue_session=False, llm_stub=llm_stub, todo_cleanup=todo_cleanup)

    assert ".Agent.Coding.todos.md" in created_files
    assert "Agent/Coding" in todo_cleanup.cleaned_agents
    assert not Path('.Agent.Coding.todos.md').exists()


def run_test_session(continue_session, llm_stub=None, todo_cleanup=None):
    def default_llm(messages):
        return ""

    llm = llm_stub if llm_stub is not None else default_llm

    io_spy = IOSpy(["\n"])
    display = ConsoleAgentDisplay(0, "Agent", io_spy)
    user_input_port = ConsoleUserInput(display.indent_level, io=io_spy)
    user_input = Input(user_input_port)
    user_input.stack("test message")

    event_bus = SimpleEventBus()
    display_factory = lambda agent_id, agent_name, indent: ConsoleAgentDisplay(indent, agent_name or agent_id, io_spy)
    display_handler = FakeDisplay(display_factory=display_factory)
    display_handler.register_display("Agent", display)

    cleanup_adapter = todo_cleanup if todo_cleanup is not None else FileSystemTodoCleanup()

    event_bus.subscribe(AgentFinishedEvent, lambda event: cleanup_adapter.cleanup_todos_for_agent(event.subagent_id))
    event_bus.subscribe(AgentCreatedEvent, display_handler.agent_created)

    test_tool_library = ToolLibraryStub(
        llm,
        io=io_spy,
        interrupts=[None],
        event_bus=event_bus,
        all_displays=display_handler
    )

    test_session_storage = SessionStorageStub()

    prompt = create_test_prompt()
    run_session(
        create_session_args(continue_session),
        BuiltinAgentLibrary(),
        display,
        event_bus,
        llm,
        prompt,
        test_session_storage,
        "Agent",
        cleanup_adapter,
        test_tool_library,
        user_input
    )

class SpyFileSystemTodoCleanup(FileSystemTodoCleanup):
    def __init__(self):
        super().__init__()
        self.cleaned_agents: list[str] = []

    def cleanup_todos_for_agent(self, agent_id: str) -> None:
        self.cleaned_agents.append(agent_id)
        super().cleanup_todos_for_agent(agent_id)
