from simple_agent.infrastructure.file_system_todo_cleanup import FileSystemTodoCleanup


def test_cleanup_all_todos_removes_todo_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".Agent.todos.md").write_text("todo", encoding="utf-8")
    (tmp_path / ".todos.md").write_text("root", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")

    cleanup = FileSystemTodoCleanup()

    cleanup.cleanup_all_todos()

    assert not (tmp_path / ".Agent.todos.md").exists()
    assert not (tmp_path / ".todos.md").exists()
    assert (tmp_path / "keep.txt").exists()
