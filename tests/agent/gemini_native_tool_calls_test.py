import json

import httpx
import pytest
from approvaltests import Options, verify

from simple_agent.infrastructure.file_event_store import FileEventStore
from simple_agent.infrastructure.gemini.gemini_client import GeminiLLM
from simple_agent.infrastructure.model_config import ModelConfig
from tests.session_test_bed import SessionTestBed
from tests.test_helpers import all_scrubbers, create_temp_file

pytestmark = pytest.mark.asyncio


class ScriptedGemini:
    """Plays back scripted Gemini interactions and records every request."""

    def __init__(self, interactions: list[dict]):
        self._interactions = list(interactions)
        self.requests: list[dict] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request):
            self.requests.append(json.loads(request.content))
            return httpx.Response(200, json=self._interactions.pop(0))

        return httpx.MockTransport(handler)

    def get(self, model_name=None, tools=None):
        config = ModelConfig(
            name="gemini",
            model="test-model",
            adapter="gemini",
            api_key="test-api-key",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            request_timeout=60,
            tool_syntax="native",
        )
        return GeminiLLM(config, tools=tools, transport=self.transport())

    def get_available_models(self):
        return ["gemini"]

    def tool_syntax(self, model_name=None):
        return "native"

    def as_approval_string(self) -> str:
        return "\n".join(
            f"# Request {index + 1} input steps\n"
            + json.dumps(request["input"], indent=2)
            for index, request in enumerate(self.requests)
        )


def completed(*steps: dict) -> dict:
    return {"id": "interactions/1", "status": "completed", "steps": list(steps)}


def text(content: str) -> dict:
    return {"type": "model_output", "content": [{"type": "text", "text": content}]}


def function_call(name: str, arguments: dict) -> dict:
    return {"type": "function_call", "id": "fc_1", "name": name, "arguments": arguments}


async def test_native_cat_call_with_a_space_in_the_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_temp_file(tmp_path, "my notes.md", "Hello world")
    gemini = ScriptedGemini(
        [
            completed(
                {"type": "thought", "signature": "SIG"},
                function_call(
                    "cat", {"filename": "my notes.md", "with_line_numbers": "true"}
                ),
            ),
            completed(text("done")),
        ]
    )

    result = (
        await SessionTestBed()
        .with_llm_provider(gemini)
        .with_user_inputs("show me my notes", "\n")
        .run()
    )

    verify(
        result.as_approval_string() + "\n" + gemini.as_approval_string(),
        options=Options().with_scrubber(all_scrubbers()),
    )


async def test_continued_session_replays_native_cat_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    create_temp_file(tmp_path, "my notes.md", "Hello world")
    event_store = FileEventStore(tmp_path / "events")
    first_gemini = ScriptedGemini(
        [
            completed(
                {"type": "thought", "signature": "SIG"},
                function_call(
                    "cat", {"filename": "my notes.md", "with_line_numbers": "true"}
                ),
            ),
            completed(text("done")),
        ]
    )
    await (
        SessionTestBed()
        .with_llm_provider(first_gemini)
        .with_event_store(event_store)
        .with_user_inputs("show me my notes", "\n")
        .run()
    )

    continued_gemini = ScriptedGemini([completed(text("done again"))])
    result = await (
        SessionTestBed()
        .with_llm_provider(continued_gemini)
        .with_event_store(event_store)
        .continuing_session()
        .with_user_inputs("what did it say?", "\n")
        .run()
    )

    verify(
        result.as_approval_string() + "\n" + continued_gemini.as_approval_string(),
        options=Options().with_scrubber(all_scrubbers()),
    )
