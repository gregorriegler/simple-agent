from pathlib import Path

from simple_agent.application.agent_definition import AgentDefinition
from simple_agent.application.agent_id import AgentId
from simple_agent.application.agent_type import AgentType
from simple_agent.application.event_bus import SimpleEventBus
from simple_agent.application.events import AgentStartedEvent, AgentFinishedEvent
from simple_agent.application.llm_stub import StubLLMProvider
from simple_agent.application.session import Session
from simple_agent.infrastructure.agent_library import BuiltinAgentLibrary
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup
from .print_spy import IOSpy
from .session_storage_stub import SessionStorageStub
from .system_prompt_generator_test import GroundRulesStub
from .test_helpers import create_session_args
from .test_tool_library import ToolLibraryFactoryStub
from .user_input_stub import UserInputStub


def test_fresh_session_should_not_display_old_todos(tmp_path, monkeypatch):
    """
    BUG: When starting a fresh session, old todos from .todos.md are briefly displayed
    because the UI loads them from the filesystem before cleanup happens.
    
    Expected: On fresh session start, the todo widget should be empty
    Actual: The todo widget briefly shows old todos before they're cleaned up
    """
    monkeypatch.chdir(tmp_path)
    # Create old .todos.md file that should NOT be displayed on fresh start
    old_todo_content = "- [ ] Old todo from previous session\n- [ ] Another old task"
    agent_id = AgentId("Agent")
    Path(agent_id.todo_filename()).write_text(old_todo_content)
    # Simulate what happens when UI loads todos during initialization
    # This happens BEFORE the session cleanup in real usage
    loaded_content_before = load_todos_as_ui_would(agent_id)
    
    # THE BUG: Old todos are visible at UI initialization time!
    # They should NOT be displayed on a fresh session start
    assert loaded_content_before == "", \
        f"BUG: Old todos should not be visible on fresh session start, but found: {loaded_content_before}"

    # Now run the session which should clean up todos
    def llm_stub(messages):
        return ""

    io_spy = IOSpy(["\n"])
    user_input_port = UserInputStub(io=io_spy)
    event_bus = SimpleEventBus()
    cleanup_adapter = FileSystemTodoCleanup()

    event_bus.subscribe(AgentFinishedEvent, 
        lambda event: cleanup_adapter.cleanup_todos_for_agent(event.agent_id) 
        if event.agent_id.has_parent() else None)

    test_session_storage = SessionStorageStub()
    agent_library = BuiltinAgentLibrary()
    tool_library_factory = ToolLibraryFactoryStub(
        llm_stub,
        io=io_spy,
        interrupts=[None],
        event_bus=event_bus,
        all_displays=None
    )
    
    session = Session(
        event_bus=event_bus,
        session_storage=test_session_storage,
        tool_library_factory=tool_library_factory,
        agent_library=agent_library,
        user_input=user_input_port,
        todo_cleanup=cleanup_adapter,
        llm_provider=StubLLMProvider.for_testing(llm_stub)
    )

    # Run the session with continue=False (fresh start)
    session.run(
        create_session_args(continue_session=False, start_message="test message"),
        agent_id,
        create_test_agent_definition()
    )

    # After cleanup, the file should be gone
    assert not Path(agent_id.todo_filename()).exists(), "Todo file should be cleaned up"
    
    # If UI refreshes now, it should get empty content
    loaded_after_cleanup = load_todos_as_ui_would(agent_id)
    assert loaded_after_cleanup == "", "After cleanup, todos should be empty"

def load_todos_as_ui_would(agent_id: AgentId) -> str:
    """Simulates how the textual UI loads todos"""
    path = Path(agent_id.todo_filename())
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8").strip()
    return content if content else ""


def create_test_agent_definition():
    return AgentDefinition(
        AgentType("Agent"), """---
name: Agent
---""",
        GroundRulesStub("Test system prompt")
    )