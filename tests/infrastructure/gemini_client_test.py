import json
from types import SimpleNamespace

import httpx
import pytest

from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.infrastructure.gemini.gemini_client import (
    GeminiClientError,
    GeminiLLM,
)
from simple_agent.infrastructure.model_config import ModelConfig


def bash_tool():
    return SimpleNamespace(
        name="bash",
        description="Execute bash commands",
        arguments=ToolArguments(
            header=[ToolArgument(name="command", description="The command")]
        ),
    )


def interaction(*texts: str) -> dict:
    return {
        "id": "interactions/123",
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [{"type": "text", "text": text} for text in texts],
            }
        ],
    }


def responding_with(response_data: dict, captured: dict | None = None):
    def handler(request):
        if captured is not None:
            captured["url"] = str(request.url)
            captured["headers"] = request.headers
            captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=response_data)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_gemini_chat_returns_text_from_model_output_step():
    chat = GeminiLLM(build_config(), transport=responding_with(interaction("hi")))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "hi"
    assert result.model == "test-model"


@pytest.mark.asyncio
async def test_gemini_chat_reports_model_from_response():
    response_data = interaction("hi") | {"model": "gemini-3.7-flash"}
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.model == "gemini-3.7-flash"


@pytest.mark.asyncio
async def test_gemini_chat_posts_to_interactions_endpoint_with_api_key_header():
    captured: dict = {}
    chat = GeminiLLM(
        build_config(base_url=None),
        transport=responding_with(interaction("hi"), captured),
    )

    await chat.call_async([{"role": "user", "content": "Hello"}])

    assert (
        captured["url"]
        == "https://generativelanguage.googleapis.com/v1beta/interactions"
    )
    assert captured["headers"]["x-goog-api-key"] == "test-api-key"
    assert captured["headers"]["Api-Revision"] == "2026-05-20"


@pytest.mark.asyncio
async def test_gemini_chat_converts_messages_to_interaction_steps():
    captured: dict = {}
    chat = GeminiLLM(
        build_config(), transport=responding_with(interaction("hi"), captured)
    )
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]

    await chat.call_async(messages)

    assert captured["body"] == {
        "model": "test-model",
        "store": False,
        "generation_config": {"tool_choice": "none"},
        "system_instruction": "You are a helpful assistant",
        "input": [
            {"type": "user_input", "content": [{"type": "text", "text": "Hello"}]},
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "Hi there!"}],
            },
            {
                "type": "user_input",
                "content": [{"type": "text", "text": "How are you?"}],
            },
        ],
    }


@pytest.mark.asyncio
async def test_gemini_chat_joins_multiple_system_messages():
    captured: dict = {}
    chat = GeminiLLM(
        build_config(), transport=responding_with(interaction("hi"), captured)
    )
    messages = [
        {"role": "system", "content": "First rule"},
        {"role": "system", "content": "Second rule"},
        {"role": "user", "content": "Hello"},
    ]

    await chat.call_async(messages)

    assert captured["body"]["system_instruction"] == "First rule\n\nSecond rule"


@pytest.mark.asyncio
async def test_gemini_chat_omits_system_instruction_when_absent():
    captured: dict = {}
    chat = GeminiLLM(
        build_config(), transport=responding_with(interaction("hi"), captured)
    )

    await chat.call_async([{"role": "user", "content": "Hello"}])

    assert "system_instruction" not in captured["body"]


@pytest.mark.asyncio
async def test_gemini_chat_forbids_native_function_calls():
    captured: dict = {}
    chat = GeminiLLM(
        build_config(), transport=responding_with(interaction("hi"), captured)
    )

    await chat.call_async([{"role": "user", "content": "Hello"}])

    assert captured["body"]["generation_config"] == {"tool_choice": "none"}


@pytest.mark.asyncio
async def test_gemini_chat_concatenates_text_of_trailing_model_output_steps():
    response_data = {
        "status": "completed",
        "steps": [
            {"type": "thought", "signature": "opaque"},
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "First part. "}],
            },
            {
                "type": "model_output",
                "content": [
                    {"type": "text", "text": "Second "},
                    {"type": "text", "text": "part."},
                ],
            },
        ],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "First part. Second part."


@pytest.mark.asyncio
async def test_gemini_chat_keeps_text_surrounding_non_text_content():
    response_data = {
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [
                    {"type": "text", "text": "this is "},
                    {"type": "image", "data": "BASE64", "mime_type": "image/png"},
                    {"type": "text", "text": "a picture"},
                ],
            }
        ],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "this is a picture"


@pytest.mark.asyncio
async def test_gemini_chat_reports_token_usage():
    response_data = interaction("hi") | {
        "usage": {
            "total_input_tokens": 100,
            "total_output_tokens": 20,
            "total_thought_tokens": 10,
            "total_tokens": 130,
        }
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.usage.input_tokens == 100
    assert result.usage.output_tokens == 30
    assert result.usage.total_tokens == 130


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_steps_missing():
    chat = GeminiLLM(build_config(), transport=responding_with({"status": "completed"}))

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response has no steps"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_model_output_has_no_text():
    response_data = {
        "status": "completed",
        "steps": [{"type": "model_output", "content": []}],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response contains no model output text"


@pytest.mark.asyncio
async def test_gemini_chat_surfaces_api_error_body():
    error_body = {
        "error": {
            "code": 400,
            "message": "API key not valid",
            "status": "INVALID_ARGUMENT",
        }
    }
    transport = httpx.MockTransport(
        lambda request: httpx.Response(400, json=error_body)
    )
    chat = GeminiLLM(build_config(), transport=transport)

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert "API key not valid" in str(error.value)


@pytest.mark.asyncio
async def test_gemini_chat_reports_error_code_when_there_is_no_message():
    response_data = {"status": "failed", "errors": [{"code": "quota/exhausted"}]}
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini interaction failed: quota/exhausted"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_interaction_failed():
    response_data = {
        "status": "failed",
        "errors": [{"code": "quota", "message": "Resource exhausted"}],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini interaction failed: quota: Resource exhausted"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_interaction_is_not_completed():
    chat = GeminiLLM(build_config(), transport=responding_with({"status": "cancelled"}))

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini interaction cancelled: no error message"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_request_fails():
    def handler(request):
        raise httpx.ConnectError("Connection failed", request=request)

    chat = GeminiLLM(build_config(), transport=httpx.MockTransport(handler))

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert "API request failed" in str(error.value)


def test_gemini_chat_raises_error_when_adapter_is_not_gemini():
    with pytest.raises(GeminiClientError) as error:
        GeminiLLM(build_config(adapter="openai"))

    assert (
        str(error.value)
        == "Configured adapter is not 'gemini'; cannot use Gemini client"
    )


@pytest.mark.asyncio
async def test_gemini_chat_skips_trailing_steps_that_are_not_model_output():
    response_data = {
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "the answer"}],
            },
            {"type": "thought", "signature": "opaque"},
        ],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "the answer"


@pytest.mark.asyncio
async def test_gemini_chat_stops_at_echoed_user_input_step():
    response_data = {
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "earlier turn"}],
            },
            {"type": "user_input", "content": [{"type": "text", "text": "Hello"}]},
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "this turn"}],
            },
        ],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "this turn"


@pytest.mark.asyncio
async def test_gemini_chat_returns_truncated_text_when_interaction_is_incomplete():
    response_data = {
        "status": "incomplete",
        "steps": [
            {"type": "model_output", "content": [{"type": "text", "text": "cut off"}]}
        ],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "cut off"


@pytest.mark.asyncio
async def test_gemini_chat_raises_model_output_error_when_there_is_no_text():
    response_data = {
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [],
                "error": {"code": 9, "message": "Recitation checked"},
            }
        ],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "Gemini model output error [9]: Recitation checked"


@pytest.mark.asyncio
async def test_gemini_chat_prefers_model_output_text_over_step_error():
    response_data = {
        "status": "completed",
        "steps": [
            {
                "type": "model_output",
                "content": [{"type": "text", "text": "partial answer"}],
                "error": {"code": 9, "message": "Recitation checked"},
            }
        ],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "partial answer"


@pytest.mark.asyncio
async def test_gemini_chat_raises_error_when_model_output_text_is_empty():
    response_data = {
        "status": "completed",
        "steps": [{"type": "model_output", "content": [{"type": "text", "text": ""}]}],
    }
    chat = GeminiLLM(build_config(), transport=responding_with(response_data))

    with pytest.raises(GeminiClientError) as error:
        await chat.call_async([{"role": "user", "content": "Hello"}])

    assert str(error.value) == "API response contains no model output text"


def build_config(
    adapter: str = "gemini",
    base_url: str | None = "https://generativelanguage.googleapis.com/v1beta",
) -> ModelConfig:
    return ModelConfig(
        name="gemini",
        model="test-model",
        adapter=adapter,
        api_key="test-api-key",
        base_url=base_url,
        request_timeout=60,
    )


@pytest.mark.asyncio
async def test_gemini_declares_tools_natively_when_provided():
    captured: dict = {}
    chat = GeminiLLM(
        build_config(),
        tools=[bash_tool()],
        transport=responding_with(interaction("ok"), captured),
    )

    await chat.call_async([{"role": "user", "content": "Hello"}])

    assert captured["body"]["tools"] == [
        {
            "function_declarations": [
                {
                    "name": "bash",
                    "description": "Execute bash commands",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "command": {"type": "STRING", "description": "The command"}
                        },
                        "required": ["command"],
                    },
                }
            ]
        }
    ]
    assert "generation_config" not in captured["body"]


@pytest.mark.asyncio
async def test_gemini_reads_function_call_into_tool_calls():
    response_data = {
        "status": "completed",
        "steps": [
            {"type": "model_output", "content": [{"type": "text", "text": "on it"}]},
            {
                "type": "function_call",
                "name": "bash",
                "arguments": {"command": "ls -la"},
            },
        ],
    }
    chat = GeminiLLM(
        build_config(), tools=[bash_tool()], transport=responding_with(response_data)
    )

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == "on it"
    assert [(c.name, c.arguments) for c in result.tool_calls] == [("bash", "ls -la")]


@pytest.mark.asyncio
async def test_gemini_allows_empty_text_when_the_model_only_calls_a_function():
    response_data = {
        "status": "completed",
        "steps": [
            {"type": "function_call", "name": "bash", "arguments": {"command": "pwd"}}
        ],
    }
    chat = GeminiLLM(
        build_config(), tools=[bash_tool()], transport=responding_with(response_data)
    )

    result = await chat.call_async([{"role": "user", "content": "Hello"}])

    assert result.content == ""
    assert [c.arguments for c in result.tool_calls] == ["pwd"]
