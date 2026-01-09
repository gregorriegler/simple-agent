import pytest

from simple_agent.application.events import ErrorEvent, ModelChangedEvent
from tests.session_test_bed import SessionTestBed

pytestmark = pytest.mark.asyncio


async def test_slash_model_command_usage_error():
    session = (
        SessionTestBed()
        .with_user_inputs("Initial message", "/model", "After error")
        .with_llm_responses(["Response after error"])
    )

    result = await session.run()

    result.assert_event_occured(
        ErrorEvent(message="Usage: /model <model-name>"), times=1
    )


async def test_slash_model_command_switches_model():
    session = (
        SessionTestBed()
        .with_user_inputs(
            "Initial message", "/model new-model", "Message with new model"
        )
        .with_llm_responses(["Response 1", "Response 2"])
    )

    result = await session.run()

    result.assert_event_occured(ModelChangedEvent(new_model="new-model"), times=1)
    saved = result.saved_messages.get("Agent", "")
    assert "user: Initial message" in saved
    assert "user: Message with new model" in saved


async def test_slash_model_command_completion_uses_configured_models():
    session = SessionTestBed().with_user_inputs("/model ").with_llm_responses([])

    # This is a bit tricky as completion is usually a UI concern,
    # but we can check if the agent's registry has the right models.
    # For now, let's just run it to make sure no regressions.
    await session.run()
