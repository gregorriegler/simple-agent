import pytest

from simple_agent.application.events import CheckpointReachedEvent
from tests.session_test_bed import SessionTestBed

pytestmark = pytest.mark.asyncio


async def test_writing_a_file_reaches_a_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    checkpoints = []
    await (
        SessionTestBed()
        .with_user_inputs("Create a file", "\n")
        .with_llm_responses(
            [
                "🛠️[create-file greeting.txt]\nHello\n🛠️[/end]",
                "🛠️[complete-task summary /]",
            ]
        )
        .on_event(CheckpointReachedEvent, checkpoints.append)
        .run()
    )

    assert len(checkpoints) == 1


async def test_reading_a_file_reaches_no_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "greeting.txt").write_text("Hello")

    checkpoints = []
    await (
        SessionTestBed()
        .with_user_inputs("Read the file", "\n")
        .with_llm_responses(["🛠️[cat greeting.txt /]", "🛠️[complete-task summary /]"])
        .on_event(CheckpointReachedEvent, checkpoints.append)
        .run()
    )

    assert len(checkpoints) == 0
