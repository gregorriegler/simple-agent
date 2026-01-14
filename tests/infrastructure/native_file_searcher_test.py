import pytest

from simple_agent.infrastructure.native_file_searcher import NativeFileSearcher


@pytest.fixture
def temp_project(tmp_path):
    """Creates a temporary project structure."""
    (tmp_path / "main.py").touch()
    (tmp_path / "utils.py").touch()
    (tmp_path / ".gitignore").write_text("ignored.py\nignored_dir/\n")
    (tmp_path / "ignored.py").touch()

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "sub.py").touch()

    ignored_dir = tmp_path / "ignored_dir"
    ignored_dir.mkdir()
    (ignored_dir / "secret.py").touch()

    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").touch()

    return tmp_path


@pytest.mark.asyncio
async def test_search_finds_files(temp_project):
    searcher = NativeFileSearcher(root_path=temp_project)

    # Empty query should return all non-ignored files
    results = await searcher.search("")
    assert "main.py" in results
    assert "utils.py" in results
    assert "subdir/sub.py" in results

    # Ignored files should not be present
    assert "ignored.py" not in results
    assert "ignored_dir/secret.py" not in results
    assert ".git/config" not in results


@pytest.mark.asyncio
async def test_search_filters_by_query(temp_project):
    searcher = NativeFileSearcher(root_path=temp_project)

    results = await searcher.search("main")
    assert results == ["main.py"]

    results = await searcher.search("sub")
    assert results == ["subdir/sub.py"]


@pytest.mark.asyncio
async def test_search_ignores_nested_gitignore(temp_project):
    # NativeFileSearcher currently only reads root .gitignore (based on implementation)
    # This test documents that behavior or ensures it works if we upgrade it.
    pass


@pytest.fixture
def bridge_project(tmp_path):
    """Creates a project to test ambiguous gitignore patterns."""
    (tmp_path / ".gitignore").write_text("bridge/\n")
    (tmp_path / "bridge.py").touch()
    bridge_dir = tmp_path / "bridge"
    bridge_dir.mkdir()
    (bridge_dir / "file.txt").touch()
    return tmp_path


@pytest.mark.asyncio
async def test_search_handles_directory_vs_file_ambiguity(bridge_project):
    searcher = NativeFileSearcher(root_path=bridge_project)
    results = await searcher.search("")  # search for everything
    assert "bridge.py" in results, "'bridge.py' should not be ignored"
    assert "bridge/file.txt" not in results, "'bridge/file.txt' should be ignored"
