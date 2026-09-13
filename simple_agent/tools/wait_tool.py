from ..application.inbox import Inbox
from ..application.tool_library import ToolArgument, ToolArguments
from ..application.tool_results import SingleToolResult
from .base_tool import BaseTool

DEFAULT_TIMEOUT = 60.0


class WaitTool(BaseTool):
    name = "wait"
    description = "Wait for a background command or subagent to finish, or for the user to say something. Returns as soon as a message is waiting for you, or when the timeout passes."
    arguments = ToolArguments(
        header=[
            ToolArgument(
                name="timeout",
                type="number",
                required=False,
                description=f"Seconds to wait at most (default {DEFAULT_TIMEOUT:.0f})",
            )
        ]
    )
    examples = [
        {
            "reasoning": "You started the tests in the background and have nothing else to do until they finish:",
            "timeout": 120,
            "result": "A message arrived.",
        },
    ]

    def __init__(self, inbox: Inbox):
        super().__init__()
        self._inbox = inbox

    async def execute(self, call):
        timeout = call.named_arguments.get("timeout", DEFAULT_TIMEOUT)
        if not isinstance(timeout, (int, float)):
            timeout = DEFAULT_TIMEOUT
        if await self._inbox.wait_for_message(timeout):
            return SingleToolResult("A message arrived.")
        return SingleToolResult(f"Nothing arrived within {timeout:g} seconds.")
