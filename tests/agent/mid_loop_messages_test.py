import pytest
from approvaltests import Options, verify

from tests.session_test_bed import SessionTestBed
from tests.test_helpers import all_scrubbers, create_temp_file

pytestmark = pytest.mark.asyncio


async def test_message_typed_while_working_is_seen_before_the_next_llm_call(tmp_path):
    temp_file = create_temp_file(tmp_path, "testfile.txt", "Hello world")

    result = (
        await SessionTestBed()
        .with_llm_responses([f"🛠️[cat {temp_file} /]", "🛠️[complete-task summary /]"])
        .with_user_inputs("Read that file", "\n")
        .with_messages_typed_while_working(["actually, stop"])
        .run()
    )

    verify(
        result.as_approval_string(), options=Options().with_scrubber(all_scrubbers())
    )
