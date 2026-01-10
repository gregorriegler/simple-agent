import json
import os

from simple_agent.infrastructure.file_session_storage import FileSessionStorage


def test_continue_session_uses_latest_session_directory(tmp_path):
    base_dir = tmp_path / "sessions"
    storage_a = FileSessionStorage.create(
        base_dir,
        continue_session=False,
        cwd=tmp_path,
    )
    storage_b = FileSessionStorage.create(
        base_dir,
        continue_session=False,
        cwd=tmp_path,
    )

    os.utime(storage_a.session_root(), (1, 1))
    os.utime(storage_b.session_root(), (2, 2))

    continued = FileSessionStorage.create(
        base_dir,
        continue_session=True,
        cwd=tmp_path,
    )

    assert continued.session_root() == storage_b.session_root()


def test_session_manifest_written(tmp_path):
    storage = FileSessionStorage.create(
        tmp_path / "sessions",
        continue_session=False,
        cwd=tmp_path,
    )

    manifest_path = storage.session_root() / "manifest.json"

    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["session_id"] == storage.session_root().name


def test_continue_session_creates_new_when_no_sessions_exist(tmp_path):
    base_dir = tmp_path / "sessions"

    storage = FileSessionStorage.create(base_dir, continue_session=True, cwd=tmp_path)

    assert storage.session_root().exists()
