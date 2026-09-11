import json

import httpx
import pytest
from approvaltests import Options, verify

from simple_agent.application.events import ToolCalledEvent
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.file_event_store import FileEventStore
from simple_agent.infrastructure.model_config import ModelConfig
from tests.session_test_bed import SessionTestBed
from tests.test_helpers import all_scrubbers, create_temp_file

pytestmark = pytest.mark.asyncio


class ScriptedClaude:
    """Plays back scripted Messages API responses and records every request."""

    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.requests: list[dict] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request):
            self.requests.append(json.loads(request.content))
            return httpx.Response(200, json=self._responses.pop(0))

        return httpx.MockTransport(handler)

    def get(self, model_name=None, tools=None):
        config = ModelConfig(
            name="claude",
            model="test-model",
            adapter="claude",
            api_key="test-api-key",
            base_url="https://api.anthropic.com/v1",
            request_timeout=60,
            tool_syntax="native",
        )
        return ClaudeLLM(config, tools=tools, transport=self.transport())

    def get_available_models(self):
        return ["claude"]

    def tool_syntax(self, model_name=None):
        return "native"

    def as_approval_string(self) -> str:
        parts = []
        for index, request in enumerate(self.requests):
            parts.append(
                f"# Request {index + 1} system\n"
                + json.dumps(request.get("system"), indent=2)
            )
            parts.append(
                f"# Request {index + 1} messages\n"
                + json.dumps(request["messages"], indent=2)
            )
        declared = self.requests[0].get("tools") or []
        parts.append(
            "# Request 1 tools\n"
            + json.dumps(
                [tool for tool in declared if tool.get("name") == "cat"], indent=2
            )
        )
        parts.append(
            "# Request 1 declared tool names\n"
            + ", ".join(tool.get("name", "") for tool in declared)
        )
        return "\n".join(parts)


def response(content: list[dict], stop_reason: str) -> dict:
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "content": content,
        "stop_reason": stop_reason,
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }


def text(content: str) -> dict:
    return response([{"type": "text", "text": content}], "end_turn")


def tool_uses(*calls: tuple[str, str, dict]) -> dict:
    return response(
        [
            {"type": "tool_use", "id": block_id, "name": name, "input": arguments}
            for block_id, name, arguments in calls
        ],
        "tool_use",
    )


async def test_native_cat_call_with_a_space_in_the_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_temp_file(tmp_path, "my notes.md", "Hello world")
    claude = ScriptedClaude(
        [
            tool_uses(
                (
                    "toolu_abc",
                    "cat",
                    {"filename": "my notes.md", "with_line_numbers": True},
                )
            ),
            text("done"),
        ]
    )

    result = (
        await SessionTestBed()
        .with_llm_provider(claude)
        .with_user_inputs("show me my notes", "\n")
        .run()
    )

    verify(
        result.as_approval_string() + "\n" + claude.as_approval_string(),
        options=Options().with_scrubber(all_scrubbers()),
    )


async def test_continued_session_replays_native_cat_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_temp_file(tmp_path, "my notes.md", "Hello world")
    event_store = FileEventStore(tmp_path / "events")
    first_claude = ScriptedClaude(
        [
            tool_uses(
                (
                    "toolu_abc",
                    "cat",
                    {"filename": "my notes.md", "with_line_numbers": True},
                )
            ),
            text("done"),
        ]
    )
    await (
        SessionTestBed()
        .with_llm_provider(first_claude)
        .with_event_store(event_store)
        .with_user_inputs("show me my notes", "\n")
        .run()
    )

    continued_claude = ScriptedClaude([text("done again")])
    result = await (
        SessionTestBed()
        .with_llm_provider(continued_claude)
        .with_event_store(event_store)
        .continuing_session()
        .with_user_inputs("what did it say?", "\n")
        .run()
    )

    verify(
        result.as_approval_string() + "\n" + continued_claude.as_approval_string(),
        options=Options().with_scrubber(all_scrubbers()),
    )


async def test_interrupted_native_call_still_gets_a_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claude = ScriptedClaude(
        [
            tool_uses(("toolu_abc", "bash", {"command": "sleep 5"})),
            text("ok"),
        ]
    )

    result = (
        await SessionTestBed()
        .with_llm_provider(claude)
        .cancelling_when(ToolCalledEvent)
        .with_user_inputs("run it", "and now?", "\n")
        .run()
    )

    verify(
        result.as_approval_string() + "\n" + claude.as_approval_string(),
        options=Options().with_scrubber(all_scrubbers()),
    )
