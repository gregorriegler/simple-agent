import subprocess

import pytest
from approvaltests import Options, verify
from approvaltests.scrubbers.scrubbers import create_regex_scrubber

from simple_agent.infrastructure.git_change_reporter import GitChangeReporter


@pytest.fixture
def repository(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    (tmp_path / "greeting.txt").write_text("Hello\n")
    git("add", ".")
    git("commit", "-m", "initial")
    return tmp_path


def test_diffs_a_changed_file(repository):
    (repository / "greeting.txt").write_text("Hello again\n")

    verify_diff(repository)


def test_diffs_a_newly_created_file(repository):
    (repository / "fresh.txt").write_text("Brand new\n")

    verify_diff(repository)


def test_diffs_changed_and_new_files_together(repository):
    (repository / "greeting.txt").write_text("Hello again\n")
    (repository / "fresh.txt").write_text("Brand new\n")

    verify_diff(repository)


def test_ignores_new_hidden_files_and_directories(repository):
    session = repository / ".simple-agent" / "sessions" / "1"
    session.mkdir(parents=True)
    (session / "events.jsonl").write_text('{"type": "AgentStartedEvent"}\n')
    (repository / ".envrc").write_text("export SECRET=1\n")

    assert GitChangeReporter(repository).diff() == ""


def test_no_diff_outside_a_repository(tmp_path):
    (tmp_path / "greeting.txt").write_text("Hello\n")

    verify_diff(tmp_path)


def verify_diff(working_directory):
    verify(
        GitChangeReporter(working_directory).diff(),
        options=Options().with_scrubber(create_blob_hash_scrubber()),
    )


def create_blob_hash_scrubber():
    return create_regex_scrubber(
        r"index [0-9a-f]+\.\.[0-9a-f]+", "index [HASH]..[HASH]"
    )
