from pathlib import Path

import pytest
from approvaltests import Options, verify

from simple_agent.application.agent_id import AgentId
from simple_agent.application.events import AgentFinishedEvent
from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup

from .session_test_bed import SessionTestBed
from .test_helpers import all_scrubbers

pytestmark = pytest.mark.asyncio


async def test_continued_session_keeps_todo_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    todo_files = [".Agent.todos.md", ".Agent.Coding.todos.md"]
    for filename in todo_files:
        Path(filename).write_text(f"content of {filename}")

    cleanup = FileSystemTodoCleanup(tmp_path)
    await (
        SessionTestBed()
        .continuing_session()
        .with_todo_cleanup(cleanup)
        .on_event(
            AgentFinishedEvent,
            lambda e: cleanup.cleanup_todos_for_agent(e.agent_id)
            if e.agent_id.has_parent()
            else None,
        )
        .run()
    )

    remaining_files = sorted([f.name for f in Path.cwd().iterdir() if f.is_file()])

    result = "Remaining files after continued session:\n" + "\n".join(remaining_files)
    verify(result, options=Options().with_scrubber(all_scrubbers()))


async def test_subagent_cleanup_deletes_subagent_todo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    created_files = set()
    original_write_text = Path.write_text

    def capture_write_text(path_obj, data, encoding=None, errors=None, newline=None):
        created_files.add(path_obj.name)
        return original_write_text(
            path_obj, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", capture_write_text)

    todo_cleanup = SpyFileSystemTodoCleanup(tmp_path)

    await (
        SessionTestBed()
        .with_llm_responses(
            [
                "🛠️[subagent coding handle-task]",
                "🛠️[write-todos]\n- [ ] Coding task\n🛠️[/end]",
                "🛠️[complete-task Subagent finished]",
                "🛠️[complete-task Root finished]",
            ]
        )
        .with_todo_cleanup(todo_cleanup)
        .on_event(
            AgentFinishedEvent,
            lambda e: todo_cleanup.cleanup_todos_for_agent(e.agent_id)
            if e.agent_id.has_parent()
            else None,
        )
        .run()
    )

    assert ".Agent-Coding.todos.md" in created_files
    assert AgentId("Agent/Coding") in todo_cleanup.cleaned_agents
    assert not Path(".Agent-Coding.todos.md").exists()


class SpyFileSystemTodoCleanup(FileSystemTodoCleanup):
    def __init__(self, root: Path):
        super().__init__(root)
        self.cleaned_agents: list[AgentId] = []

    def cleanup_todos_for_agent(self, agent_id: AgentId) -> None:
        self.cleaned_agents.append(agent_id)
        super().cleanup_todos_for_agent(agent_id)
