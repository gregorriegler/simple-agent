from pathlib import Path

from approvaltests import verify, Options

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import AgentCreatedEvent, AgentFinishedEvent
from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.application.session import Session
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from .fake_display import FakeDisplay
from .print_spy import IOSpy
from .system_prompt_generator_test import GroundRulesStub
from .test_helpers import all_scrubbers, create_session_args
from .session_storage_stub import SessionStorageStub
from .test_tool_library import ToolLibraryFactoryStub
from .user_input_stub import UserInputStub


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

    assert ".Agent-Coding.todos.md" in created_files
    assert AgentId("Agent/Coding") in todo_cleanup.cleaned_agents
    assert not Path('.Agent-Coding.todos.md').exists()


def run_test_session(continue_session, llm_stub=None, todo_cleanup=None):
    def default_llm(messages):
        return ""

    llm = llm_stub if llm_stub is not None else default_llm

    io_spy = IOSpy(["\n"])
    user_input_port = UserInputStub(io=io_spy)

    event_bus = SimpleEventBus()
    display = FakeDisplay()

    cleanup_adapter = todo_cleanup if todo_cleanup is not None else FileSystemTodoCleanup()

    event_bus.subscribe(AgentFinishedEvent, lambda event: cleanup_adapter.cleanup_todos_for_agent(event.agent_id) if event.agent_id.has_parent() else None)
    event_bus.subscribe(AgentCreatedEvent, display.agent_created)

    test_session_storage = SessionStorageStub()
    agent_library = BuiltinAgentLibrary()
    tool_library_factory = ToolLibraryFactoryStub(
        llm,
        io=io_spy,
        interrupts=[None],
        event_bus=event_bus,
        all_displays=display
    )
    session = Session(
        llm=llm,
        event_bus=event_bus,
        session_storage=test_session_storage,
        tool_library_factory=tool_library_factory,
        agent_library=agent_library,
        user_input=user_input_port,
        todo_cleanup=cleanup_adapter
    )
    agent_id = AgentId("Agent")

    session.run(
        create_session_args(continue_session, start_message="test message"),
        agent_id,
        create_test_agent_definition()
    )


def create_test_agent_definition():
    return AgentDefinition(
        AgentId("Agent"), """---
name: Agent
---""",
        GroundRulesStub("Test system prompt")
    )


class SpyFileSystemTodoCleanup(FileSystemTodoCleanup):
    def __init__(self):
        super().__init__()
        self.cleaned_agents: list[AgentId] = []

    def cleanup_todos_for_agent(self, agent_id: AgentId) -> None:
        self.cleaned_agents.append(agent_id)
        super().cleanup_todos_for_agent(agent_id)
