from __future__ import annotations

from collections.abc import Sequence

from .llm import LLM, ChatMessages, LLMResponse, TokenUsage


class StubLLM:
    def __init__(
        self, responses: Sequence[str], default: str = "", model: str = "stub-model"
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
        content = self._fallback
        if self._index < len(self._responses):
            content = self._responses[self._index]
            self._index += 1
        return LLMResponse(
            content=content, model=self._model_name, usage=TokenUsage(0, 0, 0)
        )


def create_llm_stub(responses: Sequence[str], *, default: str = "") -> LLM:
    return StubLLM(responses, default)


def _create_default_stub_llm() -> LLM:
    return create_llm_stub(
        [
            "Starting task\n🛠️[subagent orchestrator Run bash echo hello world and then complete]",
            "Subagent1 handling the orchestrator task\n🛠️[subagent coding Run bash echo hello world and then complete]",
            "Subagent2 updating todos\n🛠️[write-todos]\n- [x] Feature exploration\n- [ ] **Implementing tool**\n- [ ] Initial setup\n🛠️[/end]",
            "Subagent2 running the bash command\n🛠️[bash echo hello world]",
            "Subagent2 reading AGENTS.md\n🛠️[cat AGENTS.md]",
            "🛠️[create-file newfile.txt]\ncontent of newfile.txt\n🛠️[/end]",
            "🛠️[edit-file newfile.txt replace 1]\nnew content of newfile.txt\n🛠️[/end]",
            "🛠️[bash rm newfile.txt]",
            "🛠️[complete-task Subagent2 completed successfully]",
            "🛠️[complete-task Subagent1 completed successfully]",
            "🛠️[complete-task Main task completed successfully]",
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
                return LLMResponse(content="", model="dummy", usage=TokenUsage())

        return cls.for_testing(DummyLLM())

    @classmethod
    def for_testing(cls, llm: LLM) -> StubLLMProvider:
        provider = object.__new__(cls)
        provider._llm = llm
        return provider

    def __init__(self):
        self._llm = _create_default_stub_llm()

    def get(self, model_name: str | None = None, tools: list | None = None) -> LLM:
        return self._llm

    def get_available_models(self) -> list[str]:
        return [self._llm.model]
