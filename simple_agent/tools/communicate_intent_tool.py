from simple_agent.application.agent_id import AgentId
from simple_agent.application.intent import Intents
from simple_agent.application.tool_library import ToolArgument, ToolArguments
from simple_agent.application.tool_results import SingleToolResult, ToolResultStatus

from .base_tool import BaseTool


class CommunicateIntentTool(BaseTool):
    name = "communicate-intent"
    description = (
        "State your current overarching goal (e.g. implementing a feature, "
        "investigating a failure, or fixing a bug) so an observer knows what "
        "you are working toward and why. Always include the high-level purpose "
        "('so that...'). Do NOT call this for individual steps, tool executions, "
        "running tests, or committing changes. Only call it when the high-level "
        "pursuit changes."
    )
    arguments = ToolArguments(
        header=[],
        body=ToolArgument(
            name="intent",
            type="string",
            required=True,
            description="A single short sentence describing the current goal and its purpose (e.g. '<Objective> so that <purpose>')",
        ),
    )
    examples = [
        {
            "intent": "Extract the tool syntax parser so that agent logic is decoupled from protocol serialization",
            "result": "Intent: Extract the tool syntax parser so that agent logic is decoupled from protocol serialization",
        }
    ]

    def __init__(self, intents: Intents, agent_id: AgentId):
        super().__init__()
        self._intents = intents
        self._agent_id = agent_id

    async def execute(self, call):
        body = str(call.named_arguments.get("intent", ""))
        if not body or not body.strip():
            return SingleToolResult(
                "No intent provided", status=ToolResultStatus.FAILURE
            )

        intent = body.strip()
        self._intents.write(self._agent_id, intent)
        return SingleToolResult(f"Intent: {intent}")
