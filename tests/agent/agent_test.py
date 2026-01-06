import pytest
from approvaltests import verify, Options

from simple_agent.application.events import ErrorEvent
from tests.session_test_bed import SessionTestBed
from tests.test_helpers import (
    create_temp_file,
    create_temp_directory_structure,
    all_scrubbers,
)

pytestmark = pytest.mark.asyncio


async def test_llm_error_emits_error_event():
    result = (
        await SessionTestBed()
        .with_failing_llm("429 Too Many Requests")
        .with_user_inputs("Hello")
        .run()
    )

    error_events = result.events.get_events(ErrorEvent)
    assert len(error_events) == 1
    assert "429" in str(error_events[0])


async def test_llm_error_displayed_to_user():
    result = (
        await SessionTestBed()
        .with_failing_llm("429 Too Many Requests")
        .with_user_inputs("Hello")
        .run()
    )

    error_events = result.events.get_events(ErrorEvent)
    assert len(error_events) == 1
    assert "429" in error_events[0].message


async def test_chat_with_regular_response():
    await verify_chat(["Hello", "\n"], ["Hello! How can I help you?"])


async def test_chat_with_two_regular_responses():
    await verify_chat(["Hello", "User Answer", "\n"], ["Answer 1", "Answer 2"])


async def test_chat_with_empty_answer():
    await verify_chat(["Hello", ""], ["Test answer"])


async def test_abort():
    await verify_chat(["Test message", keyboard_interrupt], ["Test answer"])


async def test_tool_cat(tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    await verify_chat(
        ["Test message", "\n"], [f"🛠️[cat {temp_file} /]", "🛠️[complete-task summary /]"]
    )


async def test_tool_cat_integration(tmp_path):
    temp_file = create_temp_file(
        tmp_path, "integration_test.txt", "Integration test content\nLine 2"
    )
    await verify_chat(
        ["Test message", "\n"], [f"🛠️[cat {temp_file} /]", "🛠️[complete-task summary /]"]
    )


async def test_tool_ls_integration(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    await verify_chat(
        ["Test message", "\n"], [f"🛠️[ls {directory_path}]", "🛠️[complete-task summary]"]
    )


async def test_multiple_tool_calls_in_one_response(tmp_path):
    directory_path, _, temp_file, _, _ = create_temp_directory_structure(tmp_path)
    await verify_chat(
        ["Test message", "\n"],
        [
            f"I will list the files and then read one.\n🛠️[ls {directory_path} /]🛠️[cat {temp_file} /]",
            "🛠️[complete-task summary /]",
        ],
    )


async def test_chat_with_task_completion():
    await verify_chat(
        ["Say Hello", "\n"],
        ["Hello!\n🛠️[complete-task I successfully said hello /]", "ignored"],
    )


async def test_interrupt_reads_follow_up_message():
    await verify_chat(
        ["Hello", "Follow-up message", "\n"], ["Assistant response"], [], [True, False]
    )


async def test_interrupt_aborts_tool_call():
    await verify_chat(
        ["Hello", "Follow-up message", "\n"],
        ["🛠️[cat hello.txt /]", "🛠️[complete-task summary /]"],
        [],
        [True, False],
    )


async def verify_chat(inputs, answers, escape_hits=None, ctrl_c_hits=None):
    message, *remaining_inputs = inputs

    test_bed = (
        SessionTestBed()
        .with_llm_responses(answers)
        .with_user_inputs(message, *remaining_inputs)
    )

    if escape_hits:
        test_bed.with_escape_hits(escape_hits)
    if ctrl_c_hits:
        test_bed.with_ctrl_c_hits(ctrl_c_hits)

    result = await test_bed.run()
    verify(
        result.as_approval_string(), options=Options().with_scrubber(all_scrubbers())
    )


def keyboard_interrupt(_):
    raise KeyboardInterrupt()
