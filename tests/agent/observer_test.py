import pytest
from approvaltests import verify

from tests.session_test_bed import SessionTestBed

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
            "🛠️[create-file data1.txt]\nHello\n🛠️[/end]",
            "🛠️[cat data1.txt /]",
            "I will rename it.\n🛠️[complete-task renamed the file /]",
        ]
    )
    session.with_observer_responses(
        [
            "🛠️[suggest]\ndata1.txt says nothing about its content, "
            "call it greeting.txt\n🛠️[/end]\n"
            "🛠️[complete-task judged the new file /]"
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
            "🛠️[create-file data1.txt]\nHello\n🛠️[/end]",
            "🛠️[create-file greeting.txt]\nHello\n🛠️[/end]",
            "🛠️[create-file tmp2.txt]\nBye\n🛠️[/end]",
            "🛠️[cat greeting.txt /]",
            "🛠️[complete-task stored the greeting /]",
        ]
    )
    session.with_observer_responses(
        [
            "🛠️[suggest]\ntmp2.txt says nothing about its content\n🛠️[/end]\n"
            "🛠️[complete-task judged tmp2.txt /]",
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
            "🛠️[communicate-intent]\nStore the greeting in a file\n🛠️[/end]",
            "🛠️[create-file data1.txt]\nHello\n🛠️[/end]",
            "🛠️[complete-task stored the greeting /]",
        ]
    )
    session.with_observer_responses(["🛠️[complete-task judged the new file /]"])

    result = await session.run()

    verify(result.as_approval_string())


async def test_the_observer_always_receives_the_latest_intent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    session = SessionTestBed()
    session.observed_by(["naming"], BAD_NAME, GOOD_NAME)
    session.with_user_inputs("Store the greeting", "\n")
    session.with_llm_responses(
        [
            "🛠️[communicate-intent]\nStore the greeting in a file\n🛠️[/end]",
            "🛠️[create-file data1.txt]\nHello\n🛠️[/end]",
            "🛠️[communicate-intent]\nGive the file a telling name\n🛠️[/end]",
            "🛠️[create-file greeting.txt]\nHello\n🛠️[/end]",
            "🛠️[complete-task stored the greeting /]",
        ]
    )
    session.with_observer_responses(["🛠️[complete-task judged greeting.txt /]"])

    result = await session.run()

    verify(result.as_approval_string())
