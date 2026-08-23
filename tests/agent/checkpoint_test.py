import pytest
from approvaltests import Options, verify

from tests.session_test_bed import SessionTestBed
from tests.test_helpers import all_scrubbers

pytestmark = pytest.mark.asyncio


async def test_writing_a_file_reaches_a_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    await verify_checkpoints(
        ["🛠️[create-file greeting.txt]\nHello\n🛠️[/end]", "🛠️[complete-task summary /]"]
    )


async def test_reading_a_file_reaches_no_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "greeting.txt").write_text("Hello")

    await verify_checkpoints(["🛠️[cat greeting.txt /]", "🛠️[complete-task summary /]"])


async def test_failed_write_reaches_no_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "greeting.txt").write_text("Hello")

    await verify_checkpoints(
        [
            "🛠️[create-file greeting.txt]\nHello again\n🛠️[/end]",
            "🛠️[complete-task summary /]",
        ]
    )


async def verify_checkpoints(answers):
    result = (
        await SessionTestBed()
        .with_llm_responses(answers)
        .with_user_inputs("Test message", "\n")
        .run()
    )
    verify(
        result.as_approval_string(), options=Options().with_scrubber(all_scrubbers())
    )
