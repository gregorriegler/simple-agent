import pytest
from approvaltests import verify

from simple_agent.application.llm_stub import says
from tests.session_test_bed import SessionTestBed
from tests.tool_calls import complete_task, subagent

pytestmark = pytest.mark.asyncio


async def test_subagent():
    await verify_chat(
        ["Create a subagent that says hello", "\n"],
        [
            subagent("coding", "say hello"),
            says("hello", complete_task("I successfully said hello")),
        ],
    )


async def test_nested_agent_test():
    await verify_chat(
        ["Create a subagent that creates another subagent", "\n"],
        [
            subagent("orchestrator", "create another subagent"),
            subagent("coding", "say nested hello"),
            says("nested hello", complete_task("I successfully said nested hello")),
            complete_task("I successfully created another subagent"),
            complete_task("I successfully created a subagent"),
        ],
    )


async def test_agent_says_after_subagent():
    await verify_chat(
        ["Create a subagent that says hello, then say goodbye", "\n"],
        [
            subagent("coding", "say hello"),
            says("hello", complete_task("I successfully said hello")),
            "goodbye",
        ],
    )


async def test_background_subagent():
    await verify_chat(
        ["Create a background subagent that says hello", "\n"],
        [
            subagent("coding", "say hello", background=True),
            "Subagent started",
            says("hello", complete_task("I successfully said hello")),
        ],
    )


async def verify_chat(inputs, answers):
    message, *remaining_inputs = inputs

    result = (
        await SessionTestBed()
        .with_llm_responses(answers)
        .with_user_inputs(message, *remaining_inputs)
        .run()
    )

    verify(result.as_approval_string())
