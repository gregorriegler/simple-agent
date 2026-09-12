import pytest
from approvaltests import verify

from simple_agent.application.llm_stub import says
from tests.session_test_bed import SessionTestBed
from tests.tool_calls import (
    cat,
    communicate_intent,
    complete_task,
    create_file,
    suggest,
)

pytestmark = pytest.mark.asyncio

BAD_NAME = "diff --git a/data1.txt b/data1.txt\n+Hello"
GOOD_NAME = "diff --git a/greeting.txt b/greeting.txt\n+Hello"
BAD_NAME_AGAIN = "diff --git a/tmp2.txt b/tmp2.txt\n+Bye"


async def test_the_agent_receives_a_suggestion_about_a_bad_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    session = SessionTestBed()
    session.observed_by(["naming"], BAD_NAME)
    session.with_user_inputs("Store the greeting", "\n")
    session.with_llm_responses(
        [
            create_file("data1.txt", "Hello"),
            cat("data1.txt"),
            says("I will rename it.", complete_task("renamed the file")),
        ]
    )
    session.with_observer_responses(
        [
            says(
                "",
                suggest(
                    "data1.txt says nothing about its content, call it greeting.txt"
                ),
                complete_task("judged the new file"),
            )
        ]
    )

    result = await session.run()

    verify(result.as_approval_string())


async def test_the_observer_judges_the_change_it_caught_up_with(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    session = SessionTestBed()
    session.observed_by(["naming"], BAD_NAME, GOOD_NAME, BAD_NAME_AGAIN)
    session.with_user_inputs("Store the greeting", "\n")
    session.with_llm_responses(
        [
            create_file("data1.txt", "Hello"),
            create_file("greeting.txt", "Hello"),
            create_file("tmp2.txt", "Bye"),
            cat("greeting.txt"),
            complete_task("stored the greeting"),
        ]
    )
    session.with_observer_responses(
        [
            says(
                "",
                suggest("tmp2.txt says nothing about its content"),
                complete_task("judged tmp2.txt"),
            ),
        ]
    )

    result = await session.run()

    verify(result.as_approval_string())


async def test_the_observer_is_told_what_the_agent_is_trying_to_do(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    session = SessionTestBed()
    session.observed_by(["naming"], BAD_NAME)
    session.with_user_inputs("Store the greeting", "\n")
    session.with_llm_responses(
        [
            communicate_intent("Store the greeting in a file"),
            create_file("data1.txt", "Hello"),
            complete_task("stored the greeting"),
        ]
    )
    session.with_observer_responses([complete_task("judged the new file")])

    result = await session.run()

    verify(result.as_approval_string())


async def test_the_observer_always_receives_the_latest_intent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    session = SessionTestBed()
    session.observed_by(["naming"], BAD_NAME, GOOD_NAME)
    session.with_user_inputs("Store the greeting", "\n")
    session.with_llm_responses(
        [
            communicate_intent("Store the greeting in a file"),
            create_file("data1.txt", "Hello"),
            communicate_intent("Give the file a telling name"),
            create_file("greeting.txt", "Hello"),
            complete_task("stored the greeting"),
        ]
    )
    session.with_observer_responses([complete_task("judged greeting.txt")])

    result = await session.run()

    verify(result.as_approval_string())
