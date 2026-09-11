import pytest

from simple_agent.application.llm import UserMessage
from simple_agent.application.llm_stub import StubLLMProvider
from simple_agent.tools.all_tools import TOOL_DECLARATIONS


@pytest.mark.asyncio
async def test_the_default_stub_script_calls_declared_tools_with_declared_arguments():
    llm = StubLLMProvider().get()

    calls = []
    for _ in range(11):
        calls.extend((await llm.call_async([UserMessage("go")])).tool_calls)

    assert calls
    for call in calls:
        declared = {arg.name for arg in TOOL_DECLARATIONS[call.name].arguments.all}
        assert set(call.named_arguments) <= declared, call
