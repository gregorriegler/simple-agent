import pytest

from simple_agent.application.events import ModelChangedEvent, ErrorEvent
from tests.session_test_bed import SessionTestBed

pytestmark = pytest.mark.asyncio

async def test_slash_model_command_usage_error():
    session = SessionTestBed() \
        .with_user_inputs("Initial message", "/model", "After error") \
        .with_llm_responses(["Response after error"])

    result = await session.run()

    result.assert_event_occured(ErrorEvent(message="Usage: /model <model-name>"), times=1)

async def test_slash_model_command_switches_model():
    session = SessionTestBed() \
        .with_user_inputs("Initial message", "/model new-model", "Message with new model") \
        .with_llm_responses(["Response 1", "Response 2"])

    result = await session.run()

    result.assert_event_occured(ModelChangedEvent(new_model="new-model"), times=1)
    assert "user: Initial message" in result.saved_messages
    assert "user: Message with new model" in result.saved_messages
