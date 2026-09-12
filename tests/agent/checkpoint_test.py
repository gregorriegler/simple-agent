import pytest
from approvaltests import Options, verify

from tests.session_test_bed import SessionTestBed
from tests.test_helpers import all_scrubbers
from tests.tool_calls import cat, complete_task, create_file

pytestmark = pytest.mark.asyncio


async def test_writing_a_file_reaches_a_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    await verify_checkpoints(
        [create_file("greeting.txt", "Hello"), complete_task("summary")]
    )


async def test_reading_a_file_reaches_no_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "greeting.txt").write_text("Hello")

    await verify_checkpoints([cat("greeting.txt"), complete_task("summary")])


async def test_failed_write_reaches_no_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "greeting.txt").write_text("Hello")

    await verify_checkpoints(
        [
            create_file("greeting.txt", "Hello again"),
            complete_task("summary"),
        ]
    )


async def verify_checkpoints(answers):
    session = SessionTestBed()
    session.with_llm_responses(answers)
    session.with_user_inputs("Test message", "\n")

    result = await session.run()

    verify(
        result.as_approval_string(), options=Options().with_scrubber(all_scrubbers())
    )
