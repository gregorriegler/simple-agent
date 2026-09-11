from types import SimpleNamespace

import pytest

from simple_agent.application.llm import LLMResponse, TokenUsage, UserMessage
from simple_agent.application.text_response import EmojiToolCallsLLM
from simple_agent.application.tool_library import (
    RawToolCall,
    ToolArgument,
    ToolArguments,
)

pytestmark = pytest.mark.asyncio

BASH = SimpleNamespace(
    name="bash",
    arguments=ToolArguments(header=[ToolArgument(name="command", description="")]),
)
CAT = SimpleNamespace(
    name="cat",
    arguments=ToolArguments(
        header=[
            ToolArgument(name="filename", description=""),
            ToolArgument(name="with_line_numbers", description="", type="bool"),
        ]
    ),
)


class TextOnlyLLM:
    def __init__(self, answer: str):
        self.answer = answer
        self.received: list = []

    @property
    def model(self) -> str:
        return "text-model"

    async def call_async(self, messages) -> LLMResponse:
        self.received.append(list(messages))
        return LLMResponse(
            answer=self.answer,
            model=self.model,
            usage=TokenUsage(3, 4, 7),
            thought="hmm",
        )


async def test_binds_the_emoji_calls_in_the_answer_to_the_given_tools():
    llm = EmojiToolCallsLLM(
        TextOnlyLLM("on it\n🛠️[cat notes.md with_line_numbers /]"), [BASH, CAT]
    )

    response = await llm.call_async([UserMessage("hi")])

    assert response.tool_calls == [
        RawToolCall("cat", {"filename": "notes.md", "with_line_numbers": True})
    ]
    assert response.tool_calls[0].declaration is CAT.arguments
    assert response.message == "on it"
    assert response.answer == "on it\n🛠️[cat notes.md with_line_numbers /]"


async def test_a_call_to_an_unknown_tool_leaves_the_answer_as_text():
    llm = EmojiToolCallsLLM(TextOnlyLLM("try\n🛠️[rm -rf / /]"), [BASH])

    response = await llm.call_async([UserMessage("hi")])

    assert response.tool_calls == []
    assert response.message == "try\n🛠️[rm -rf / /]"


async def test_passes_messages_in_and_the_rest_of_the_response_through():
    inner = TextOnlyLLM("just text")
    llm = EmojiToolCallsLLM(inner, [BASH])

    response = await llm.call_async([UserMessage("hi")])

    assert inner.received == [[UserMessage("hi")]]
    assert llm.model == "text-model"
    assert (response.model, response.usage, response.thought) == (
        "text-model",
        TokenUsage(3, 4, 7),
        "hmm",
    )
    assert response.message == "just text"
