from __future__ import annotations

from collections.abc import Sequence

from .llm import ChatMessages, LLM


def create_llm_stub(responses: Sequence[str], *, default: str = "") -> LLM:
    index = 0
    fallback = responses[-1] if responses else default

    def llm_stub(system_prompt: str, messages: ChatMessages) -> str:
        nonlocal index
        if index < len(responses):
            response = responses[index]
            index += 1
            return response
        return fallback

    return llm_stub
