import pytest

from simple_agent.application.llm import UserMessage
from simple_agent.application.llm_stub import create_llm_stub, says
from simple_agent.application.tool_library import ToolCall

pytestmark = pytest.mark.asyncio

CAT = ToolCall("cat", {"filename": "a.txt"})


async def test_a_scripted_tool_call_is_an_answer_without_words():
    llm = create_llm_stub([CAT])

    response = await llm.call_async([UserMessage("go")])

    assert response.answer == ""
    assert response.tool_calls == [CAT]


async def test_says_scripts_words_with_the_calls_they_lead_to():
    llm = create_llm_stub([says("reading it", CAT)])

    response = await llm.call_async([UserMessage("go")])

    assert response.answer == "reading it"
    assert response.tool_calls == [CAT]


async def test_the_last_scripted_call_repeats():
    llm = create_llm_stub([CAT])
    await llm.call_async([UserMessage("go")])

    response = await llm.call_async([UserMessage("again")])

    assert response.tool_calls == [CAT]
