from approvaltests import verify, Options

from tests.session_test_bed import SessionTestBed
from tests.test_helpers import create_temp_file, create_temp_directory_structure, all_scrubbers


def test_llm_error_emits_error_event():
    result = SessionTestBed() \
        .with_failing_llm("429 Too Many Requests") \
        .with_user_inputs("Hello") \
        .run()

    assert len(result.error_events) == 1
    assert "429" in str(result.error_events[0])


def test_llm_error_displayed_to_user():
    result = SessionTestBed() \
        .with_failing_llm("429 Too Many Requests") \
        .with_user_inputs("Hello") \
        .run()

    error_display_events = [e for e in result.display_events if e["event"] == "error_occurred"]
    assert len(error_display_events) == 1
    assert "429" in error_display_events[0]["payload"]


def test_chat_with_regular_response():
    verify_chat(["Hello", "\n"], ["Hello! How can I help you?"])


def test_chat_with_two_regular_responses():
    verify_chat(["Hello", "User Answer", "\n"], ["Answer 1", "Answer 2"])


def test_chat_with_empty_answer():
    verify_chat(["Hello", ""], ["Test answer"])


def test_abort():
    verify_chat(["Test message", keyboard_interrupt], ["Test answer"])


def test_tool_cat(tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")
    verify_chat(["Test message", "\n"], [f"🛠️[cat {temp_file} /]", "🛠️[complete-task summary /]"])


def test_tool_cat_integration(tmp_path):
    temp_file = create_temp_file(tmp_path, "integration_test.txt", "Integration test content\nLine 2")
    verify_chat(["Test message", "\n"], [f"🛠️[cat {temp_file} /]", "🛠️[complete-task summary /]"])


def test_tool_ls_integration(tmp_path):
    directory_path, _, _, _, _ = create_temp_directory_structure(tmp_path)
    verify_chat(["Test message", "\n"], [f"🛠️[ls {directory_path}]", "🛠️[complete-task summary]"])


def test_multiple_tool_calls_in_one_response(tmp_path):
    directory_path, _, temp_file, _, _ = create_temp_directory_structure(tmp_path)
    verify_chat(["Test message", "\n"], [f"I will list the files and then read one.\n🛠️[ls {directory_path} /]🛠️[cat {temp_file} /]", "🛠️[complete-task summary /]"])


def test_chat_with_task_completion():
    verify_chat(
        ["Say Hello", "\n"], [
            "Hello!\n🛠️[complete-task I successfully said hello /]",
            "ignored"
        ]
    )


def test_interrupt_reads_follow_up_message():
    verify_chat(["Hello", "Follow-up message", "\n"], ["Assistant response"], [], [True, False])


def test_interrupt_aborts_tool_call():
    verify_chat(
        ["Hello", "Follow-up message", "\n"], ["🛠️[cat hello.txt /]", "🛠️[complete-task summary /]"], [], [True, False]
    )


def verify_chat(inputs, answers, escape_hits=None, ctrl_c_hits=None):
    message, *remaining_inputs = inputs

    test_bed = SessionTestBed() \
        .with_llm_responses(answers) \
        .with_user_inputs(message, *remaining_inputs)

    if escape_hits:
        test_bed.with_escape_hits(escape_hits)
    if ctrl_c_hits:
        test_bed.with_ctrl_c_hits(ctrl_c_hits)

    result = test_bed.run()
    verify(result.as_approval_string(), options=Options().with_scrubber(all_scrubbers()))


def keyboard_interrupt(_):
    raise KeyboardInterrupt()
