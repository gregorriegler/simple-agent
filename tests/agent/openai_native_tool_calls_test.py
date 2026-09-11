import json

import httpx
import pytest
from approvaltests import Options, verify

from simple_agent.application.events import ToolCalledEvent
from simple_agent.infrastructure.file_event_store import FileEventStore
from simple_agent.infrastructure.model_config import ModelConfig
from simple_agent.infrastructure.openai.openai_client import OpenAILLM
from tests.session_test_bed import SessionTestBed
from tests.test_helpers import all_scrubbers, create_temp_file

pytestmark = pytest.mark.asyncio


class ScriptedOpenAI:
    """Plays back scripted chat completions and records every request."""

    def __init__(self, completions: list[dict]):
        self._completions = list(completions)
        self.requests: list[dict] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request):
            self.requests.append(json.loads(request.content))
            return httpx.Response(200, json=self._completions.pop(0))

        return httpx.MockTransport(handler)

    def get(self, model_name=None, tools=None):
        config = ModelConfig(
            name="openai",
            model="test-model",
            adapter="openai",
            api_key="test-api-key",
            base_url="https://api.openai.com/v1",
            request_timeout=60,
        )
        return OpenAILLM(config, tools=tools, transport=self.transport())

    def get_available_models(self):
        return ["openai"]

    def tool_syntax(self, model_name=None):
        return "native"

    def as_approval_string(self) -> str:
        parts = []
        for index, request in enumerate(self.requests):
            parts.append(
                f"# Request {index + 1} messages\n"
                + json.dumps(request["messages"], indent=2)
            )
        declared = self.requests[0].get("tools") or []
        parts.append(
            "# Request 1 tools\n"
            + json.dumps(
                [
                    tool
                    for tool in declared
                    if tool.get("function", {}).get("name") == "cat"
                ],
                indent=2,
            )
        )
        parts.append(
            "# Request 1 declared tool names\n"
            + ", ".join(tool.get("function", {}).get("name", "") for tool in declared)
        )
        return "\n".join(parts)


def completion(message: dict) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", **message}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def text(content: str) -> dict:
    return {"content": content}


def tool_calls(*calls: tuple[str, str, dict]) -> dict:
    return {
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }
            for call_id, name, arguments in calls
        ],
    }


async def test_native_cat_call_with_a_space_in_the_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_temp_file(tmp_path, "my notes.md", "Hello world")
    openai = ScriptedOpenAI(
        [
            completion(
                tool_calls(
                    (
                        "call_abc",
                        "cat",
                        {"filename": "my notes.md", "with_line_numbers": True},
                    )
                )
            ),
            completion(text("done")),
        ]
    )

    result = (
        await SessionTestBed()
        .with_llm_provider(openai)
        .with_user_inputs("show me my notes", "\n")
        .run()
    )

    verify(
        result.as_approval_string() + "\n" + openai.as_approval_string(),
        options=Options().with_scrubber(all_scrubbers()),
    )


async def test_continued_session_replays_native_cat_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_temp_file(tmp_path, "my notes.md", "Hello world")
    event_store = FileEventStore(tmp_path / "events")
    first_openai = ScriptedOpenAI(
        [
            completion(
                tool_calls(
                    (
                        "call_abc",
                        "cat",
                        {"filename": "my notes.md", "with_line_numbers": True},
                    )
                )
            ),
            completion(text("done")),
        ]
    )
    await (
        SessionTestBed()
        .with_llm_provider(first_openai)
        .with_event_store(event_store)
        .with_user_inputs("show me my notes", "\n")
        .run()
    )

    continued_openai = ScriptedOpenAI([completion(text("done again"))])
    result = await (
        SessionTestBed()
        .with_llm_provider(continued_openai)
        .with_event_store(event_store)
        .continuing_session()
        .with_user_inputs("what did it say?", "\n")
        .run()
    )

    verify(
        result.as_approval_string() + "\n" + continued_openai.as_approval_string(),
        options=Options().with_scrubber(all_scrubbers()),
    )


async def test_interrupted_native_call_still_gets_a_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    openai = ScriptedOpenAI(
        [
            completion(tool_calls(("call_abc", "bash", {"command": "sleep 5"}))),
            completion(text("ok")),
        ]
    )

    result = (
        await SessionTestBed()
        .with_llm_provider(openai)
        .cancelling_when(ToolCalledEvent)
        .with_user_inputs("run it", "and now?", "\n")
        .run()
    )

    verify(
        result.as_approval_string() + "\n" + openai.as_approval_string(),
        options=Options().with_scrubber(all_scrubbers()),
    )
