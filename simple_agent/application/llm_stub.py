from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from .llm import LLM, ChatMessages, LLMResponse, TokenUsage
from .tool_library import ToolCall

StubResponse = str | LLMResponse


class StubLLM:
    """
    Answers a scripted sequence, then repeats its last answer. A plain
    string is a text-only answer; an LLMResponse carries its tool calls.
    """

    def __init__(
        self,
        responses: Sequence[StubResponse],
        default: str = "",
        model: str = "stub-model",
    ):
        self._responses = responses
        self._default = default
        self._model_name = model
        self._index = 0
        self._fallback = responses[-1] if responses else default

    @property
    def model(self) -> str:
        return self._model_name

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        response = self._fallback
        if self._index < len(self._responses):
            response = self._responses[self._index]
            self._index += 1
        if isinstance(response, LLMResponse):
            return replace(response, model=self._model_name)
        return LLMResponse(
            answer=response, model=self._model_name, usage=TokenUsage(0, 0, 0)
        )


def create_llm_stub(responses: Sequence[StubResponse], *, default: str = "") -> LLM:
    return StubLLM(responses, default)


def _says(text: str, *calls: ToolCall) -> LLMResponse:
    return LLMResponse(answer=text, tool_calls=list(calls), usage=TokenUsage(0, 0, 0))


def _create_default_stub_llm() -> LLM:
    task = "Run bash echo hello world and then complete"
    return create_llm_stub(
        [
            _says(
                "Starting task",
                ToolCall(
                    "subagent",
                    {"agenttype": "orchestrator", "task_description": task},
                ),
            ),
            _says(
                "Subagent1 handling the orchestrator task",
                ToolCall("subagent", {"agenttype": "coding", "task_description": task}),
            ),
            _says(
                "Subagent2 updating todos",
                ToolCall(
                    "write-todos",
                    {
                        "content": "- [x] Feature exploration\n"
                        "- [ ] **Implementing tool**\n"
                        "- [ ] Initial setup"
                    },
                ),
            ),
            _says(
                "Subagent2 running the bash command",
                ToolCall("bash", {"command": "echo hello world"}),
            ),
            _says(
                "Subagent2 reading AGENTS.md",
                ToolCall("cat", {"filename": "AGENTS.md"}),
            ),
            _says(
                "",
                ToolCall(
                    "create-file",
                    {"filename": "newfile.txt", "content": "content of newfile.txt"},
                ),
            ),
            _says(
                "",
                ToolCall(
                    "replace-file-content",
                    {
                        "filename": "newfile.txt",
                        "replace_mode": "single",
                        "content": "content of newfile.txt@@@new content of newfile.txt",
                    },
                ),
            ),
            _says("", ToolCall("bash", {"command": "rm newfile.txt"})),
            _says(
                "",
                ToolCall(
                    "complete-task", {"summary": "Subagent2 completed successfully"}
                ),
            ),
            _says(
                "",
                ToolCall(
                    "complete-task", {"summary": "Subagent1 completed successfully"}
                ),
            ),
            _says(
                "",
                ToolCall(
                    "complete-task", {"summary": "Main task completed successfully"}
                ),
            ),
        ]
    )


class StubLLMProvider:
    @classmethod
    def dummy(cls) -> StubLLMProvider:
        class DummyLLM:
            @property
            def model(self) -> str:
                return "dummy"

            async def call_async(self, messages):
                return LLMResponse(answer="", model="dummy", usage=TokenUsage())

        provider = object.__new__(cls)
        provider._llm = DummyLLM()
        return provider

    def __init__(self):
        self._llm = _create_default_stub_llm()

    def get(self, model_name: str | None = None, tools: list | None = None) -> LLM:
        return self._llm

    def get_available_models(self) -> list[str]:
        return [self._llm.model]
