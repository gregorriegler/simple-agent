from __future__ import annotations

from collections.abc import Sequence

from .llm import ChatMessages, LLM


def create_llm_stub(responses: Sequence[str], *, default: str = "") -> LLM:
    index = 0
    fallback = responses[-1] if responses else default

    def llm_stub(messages: ChatMessages) -> str:
        nonlocal index
        if index < len(responses):
            response = responses[index]
            index += 1
            return response
        return fallback

    return llm_stub


def _create_default_stub_llm() -> LLM:
    return create_llm_stub(
        [
            "Starting task\n🛠️ subagent orchestrator Run bash echo hello world and then complete",
            "Subagent1 handling the orchestrator task\n🛠️ subagent coding Run bash echo hello world and then complete",
            "Subagent2 updating todos\n🛠️ write-todos\n- [x] Feature exploration\n- [ ] **Implementing tool**\n- [ ] Initial setup\n🛠️🔚",
            "Subagent2 running the bash command\n🛠️ bash echo hello world",
            "Subagent2 reading AGENTS.md\n🛠️ cat AGENTS.md",
            "🛠️ create-file newfile.txt\ncontent of newfile.txt\n",
            "🛠️ edit-file newfile.txt replace 1\nnew content of newfile.txt\n",
            "🛠️ bash rm newfile.txt",
            "🛠️ complete-task Subagent2 completed successfully",
            "🛠️ complete-task Subagent1 completed successfully",
            "🛠️ complete-task Main task completed successfully"
        ]
    )


class StubLLMProvider:

    @classmethod
    def dummy(cls) -> 'StubLLMProvider':
        return cls.for_testing(lambda messages: '')

    @classmethod
    def for_testing(cls, llm: LLM) -> 'StubLLMProvider':
        provider = object.__new__(cls)
        provider._llm = llm
        return provider

    def __init__(self):
        self._llm = _create_default_stub_llm()

    def get(self, model_name: str | None = None) -> LLM:
        return self._llm
