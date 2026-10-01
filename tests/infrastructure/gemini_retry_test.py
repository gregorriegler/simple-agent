import json
from unittest.mock import patch

import httpx
import pytest
from approvaltests import verify

from simple_agent.application.llm import UserMessage
from simple_agent.infrastructure.gemini.gemini_client import (
    GeminiClientError,
    GeminiLLM,
)
from simple_agent.infrastructure.model_config import ModelConfig

SUCCESS = {
    "status": "completed",
    "steps": [
        {"type": "model_output", "content": [{"type": "text", "text": "success"}]}
    ],
    "usage": {},
}


def build_config() -> ModelConfig:
    return ModelConfig(
        name="gemini",
        model="test-model",
        adapter="gemini",
        api_key="test-api-key",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        request_timeout=60,
    )


@pytest.mark.asyncio
async def test_gemini_retries_on_timeout():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(200, json=SUCCESS)

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))

    with patch("asyncio.sleep", return_value=None):
        result = await client.call_async([UserMessage("hello")])

    assert result.answer == "success"
    assert call_count == 2


MALFORMED_TOOL_CALL = {
    "error": {
        "message": "Model generated invalid JSON syntax. Please retry the request.",
        "code": "malformed_tool_call",
    }
}


@pytest.mark.asyncio
async def test_gemini_retries_a_malformed_tool_call():
    responses = [httpx.Response(400, json=MALFORMED_TOOL_CALL)]

    def handler(request):
        return responses.pop(0) if responses else httpx.Response(200, json=SUCCESS)

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))

    with patch("asyncio.sleep", return_value=None):
        result = await client.call_async([UserMessage("hello")])

    assert result.answer == "success"


@pytest.mark.asyncio
async def test_gemini_retries_a_malformed_tool_call_with_the_error_as_a_hint():
    inputs = []
    responses = [httpx.Response(400, json=MALFORMED_TOOL_CALL)] * 2

    def handler(request):
        inputs.append(json.loads(request.content)["input"])
        return responses.pop(0) if responses else httpx.Response(200, json=SUCCESS)

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))
    with patch("asyncio.sleep", return_value=None):
        await client.call_async([UserMessage("hello")])

    verify("\n\n".join(json.dumps(i, indent=2) for i in inputs))


async def delays_before_success(*failures: httpx.Response) -> list[float]:
    responses = list(failures)

    def handler(request):
        return responses.pop(0) if responses else httpx.Response(200, json=SUCCESS)

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))
    with patch("asyncio.sleep", return_value=None) as sleep:
        await client.call_async([UserMessage("hello")])
    return [call.args[0] for call in sleep.call_args_list]


@pytest.mark.asyncio
async def test_gemini_waits_as_long_as_retry_after_asks():
    delays = await delays_before_success(
        httpx.Response(500, headers={"Retry-After": "7"}),
        httpx.Response(500),
        httpx.Response(500, headers={"Retry-After": "3600"}),
        httpx.Response(500, headers={"Retry-After": "soon"}),
    )

    assert delays == [7, 2, 60, 2]


@pytest.mark.asyncio
async def test_gemini_does_not_retry_other_bad_requests():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(400, json={"error": {"code": "invalid_argument"}})

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(GeminiClientError):
            await client.call_async([UserMessage("hello")])

    assert call_count == 1


@pytest.mark.asyncio
async def test_gemini_eventually_fails_after_5_retries():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        return httpx.Response(500)

    client = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(GeminiClientError) as excinfo:
            await client.call_async([UserMessage("hello")])

    assert call_count == 6
    assert "500" in str(excinfo.value)
