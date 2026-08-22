import pytest

from simple_agent.application.brain import Brain
from simple_agent.application.llm import LLMResponse
from simple_agent.application.tool_library import MessageAndParsedTools, RawToolCall


class FakeLLM:
    def __init__(self, response: LLMResponse):
        self._response = response

    @property
    def model(self) -> str:
        return "fake-model"

    async def call_async(self, messages) -> LLMResponse:
        return self._response


class RecordingTools:
    def __init__(self):
        self.resolved = None
        self.parsed_text = None

    def resolve_tool_calls(self, tool_calls, message) -> MessageAndParsedTools:
        self.resolved = (tool_calls, message)
        return MessageAndParsedTools(message=message, tools=["RESOLVED"])

    def parse_message_and_tools(self, text) -> MessageAndParsedTools:
        self.parsed_text = text
        return MessageAndParsedTools(message=text, tools=["PARSED"])


def brain_with(llm, tools) -> Brain:
    return Brain(name="agent", system_prompt="sp", llm=llm, tools=tools)


@pytest.mark.asyncio
async def test_binds_structured_tool_calls_when_the_llm_provides_them():
    calls = [RawToolCall(name="bash", arguments="echo hi")]
    llm = FakeLLM(LLMResponse(content="running it", tool_calls=calls))
    tools = RecordingTools()

    _, parsed = await brain_with(llm, tools).respond([])

    assert tools.resolved == (calls, "running it")
    assert tools.parsed_text is None
    assert parsed.tools == ["RESOLVED"]


@pytest.mark.asyncio
async def test_parses_the_text_when_there_are_no_structured_tool_calls():
    llm = FakeLLM(LLMResponse(content="🛠️[bash echo hi /]"))
    tools = RecordingTools()

    _, parsed = await brain_with(llm, tools).respond([])

    assert tools.parsed_text == "🛠️[bash echo hi /]"
    assert tools.resolved is None
    assert parsed.tools == ["PARSED"]
