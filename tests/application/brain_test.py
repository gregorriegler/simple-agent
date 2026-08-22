import pytest

from simple_agent.application.brain import Brain
from simple_agent.application.llm import LLMResponse


class FakeLLM:
    def __init__(self, response: LLMResponse):
        self._response = response
        self.received = None

    @property
    def model(self) -> str:
        return "fake-model"

    async def call_async(self, messages) -> LLMResponse:
        self.received = messages
        return self._response


@pytest.mark.asyncio
async def test_relays_the_llm_response_for_the_given_messages():
    response = LLMResponse(answer="hi")
    llm = FakeLLM(response)
    brain = Brain(name="agent", system_prompt="sp", llm=llm, tools=None)

    result = await brain.respond([{"role": "user", "content": "hello"}])

    assert result is response
    assert llm.received == [{"role": "user", "content": "hello"}]
