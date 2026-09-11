import json
from types import SimpleNamespace

import httpx
import pytest

from simple_agent.application.llm import SystemMessage, UserMessage
from simple_agent.application.tool_library import (
    ToolArgument,
    ToolArguments,
    ToolCall,
)
from simple_agent.infrastructure.claude.claude_client import (
    ClaudeClientError,
    ClaudeLLM,
)
from simple_agent.infrastructure.model_config import ModelConfig


@pytest.mark.asyncio
async def test_claude_chat_returns_content_text():
    response_data = {
        "content": [{"type": "text", "text": "assistant response"}],
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    system_prompt = "system prompt"

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    chat = ClaudeLLM(build_config(), transport=transport)
    messages = [
        SystemMessage(system_prompt),
        UserMessage("Hello"),
    ]

    result = await chat.call_async(messages)

    assert result.answer == "assistant response"
    assert result.model == "test-model"
    assert result.usage is not None
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.total_tokens == 30


@pytest.mark.asyncio
async def test_claude_chat_raises_error_when_content_missing():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))

    chat = ClaudeLLM(build_config(), transport=transport)

    with pytest.raises(ClaudeClientError) as error:
        await chat.call_async([UserMessage("Hello")])

    assert str(error.value) == "API response missing 'content' field"


@pytest.mark.asyncio
async def test_claude_chat_raises_error_when_request_fails():
    def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    transport = httpx.MockTransport(handler)
    chat = ClaudeLLM(build_config(), transport=transport)

    with pytest.raises(ClaudeClientError) as error:
        await chat.call_async([UserMessage("Hello")])

    assert "API request failed" in str(error.value)


def build_config(base_url: str | None = None) -> ModelConfig:
    return ModelConfig(
        name="claude",
        model="test-model",
        adapter="claude",
        api_key="test-api-key",
        base_url=base_url,
        request_timeout=60,
    )


def build_tool(name: str) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        description=f"{name} tool",
        arguments=ToolArguments(
            header=[ToolArgument(name="filename", description="", required=True)]
        ),
    )


@pytest.mark.asyncio
async def test_claude_chat_declares_its_tools():
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200, json={"content": [{"type": "text", "text": "ok"}], "usage": {}}
        )

    chat = ClaudeLLM(
        build_config(),
        tools=[build_tool("cat")],
        transport=httpx.MockTransport(handler),
    )

    await chat.call_async([UserMessage("Hello")])

    assert [tool["name"] for tool in requests[0]["tools"]] == ["cat"]
    assert requests[0]["tools"][0]["input_schema"]["required"] == ["filename"]


@pytest.mark.asyncio
async def test_claude_chat_reads_tool_use_blocks_into_bound_calls():
    response_data = {
        "content": [
            {"type": "text", "text": "Let me look."},
            {
                "type": "tool_use",
                "id": "toolu_abc",
                "name": "cat",
                "input": {"filename": "notes.md"},
            },
        ],
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )
    chat = ClaudeLLM(build_config(), tools=[build_tool("cat")], transport=transport)

    result = await chat.call_async([UserMessage("show notes")])

    assert result.answer == "Let me look."
    assert result.tool_calls == [
        ToolCall(
            "cat", {"filename": "notes.md"}, provider_state={"native_id": "toolu_abc"}
        )
    ]


@pytest.mark.asyncio
async def test_claude_chat_without_tools_declares_none():
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200, json={"content": [{"type": "text", "text": "ok"}], "usage": {}}
        )

    chat = ClaudeLLM(build_config(), transport=httpx.MockTransport(handler))

    await chat.call_async([UserMessage("Hello")])

    assert "tools" not in requests[0]
