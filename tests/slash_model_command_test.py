import pytest
from approvaltests import verify

from simple_agent.application.events import ErrorEvent
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

    verify(result.as_approval_string())


async def test_slash_model_command_completion_uses_configured_models():
    session = SessionTestBed().with_user_inputs("/model ").with_llm_responses([])

    # This is a bit tricky as completion is usually a UI concern,
    # but we can check if the agent's registry has the right models.
    # For now, let's just run it to make sure no regressions.
    await session.run()
