from simple_agent.application.agent_types import AgentTypes
from simple_agent.application.intent import Intents
from simple_agent.application.subagent_spawner import SubagentSpawner
from simple_agent.application.tool_library import (
    AssistantTurn,
    Tool,
    ToolDeclaration,
    ToolInvocation,
    ToolLibrary,
)
from simple_agent.application.tool_library_factory import (
    ToolContext,
    ToolLibraryFactory,
)

from .bash_tool import BashTool
from .cat_tool import CatTool
from .communicate_intent_tool import CommunicateIntentTool
from .complete_task_tool import CompleteTaskTool
from .create_file_tool import CreateFileTool
from .ls_tool import LsTool
from .replace_file_content_tool import ReplaceFileContentTool
from .subagent_tool import SubagentTool
from .suggest_tool import SuggestTool
from .wait_tool import WaitTool
from .write_todos_tool import WriteTodosTool

OBSERVER_ONLY_TOOLS = ("suggest",)

TOOL_DECLARATIONS: dict[str, ToolDeclaration] = {
    tool.name: tool
    for tool in (
        BashTool,
        CatTool,
        CommunicateIntentTool,
        CompleteTaskTool,
        CreateFileTool,
        LsTool,
        ReplaceFileContentTool,
        SubagentTool,
        SuggestTool,
        WaitTool,
        WriteTodosTool,
    )
}


class AllTools(ToolLibrary):
    def __init__(
        self,
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        agent_types: AgentTypes,
        intents: Intents,
    ):
        self.tool_context = tool_context
        self._spawner = spawner
        self._agent_types = agent_types
        self._intents = intents
        self.tool_keys = tool_context.tool_keys if tool_context.tool_keys else []

        static_tools = self._create_static_tools()
        dynamic_tools = self._discover_dynamic_tools()
        self.tools: list[Tool] = static_tools + dynamic_tools
        self.tool_dict = {getattr(tool, "name", ""): tool for tool in self.tools}

    def _create_static_tools(self):
        tool_map = {
            "write_todos": lambda: WriteTodosTool(
                str(self.tool_context.agent_id.todo_filename())
            ),
            "ls": lambda: LsTool(),
            "cat": lambda: CatTool(),
            "create_file": lambda: CreateFileTool(),
            "replace_file_content": lambda: ReplaceFileContentTool(),
            "complete_task": lambda: CompleteTaskTool(),
            "communicate_intent": lambda: CommunicateIntentTool(
                self._intents, self.tool_context.agent_id
            ),
            "suggest": lambda: SuggestTool(),
            "bash": lambda: BashTool(self.tool_context.inbox.stack),
            "wait": lambda: WaitTool(self.tool_context.inbox),
            "subagent": lambda: SubagentTool(self._spawner, self._agent_types),
        }

        if not self.tool_keys:
            tools = [
                factory()
                for key, factory in tool_map.items()
                if key not in OBSERVER_ONLY_TOOLS
            ]
            return [tool for tool in tools if tool is not None]

        tools = []
        for key in self.tool_keys:
            if key in tool_map:
                tool = tool_map[key]()
                if tool is not None:
                    tools.append(tool)
        return tools

    def resolve_tool_calls(self, tool_calls, message) -> AssistantTurn:
        """Pair each bound call with the tool that runs it."""
        return AssistantTurn(
            message=message,
            invocations=[
                ToolInvocation(call, self.tool_dict[call.name]) for call in tool_calls
            ],
        )

    async def execute_tool_call(self, invocation):
        return await invocation.execute()

    def _discover_dynamic_tools(self):
        return []


class AllToolsFactory(ToolLibraryFactory):
    def __init__(self, intents: Intents):
        self._intents = intents

    def create(
        self,
        tool_context: ToolContext,
        spawner: SubagentSpawner,
        agent_types: AgentTypes,
    ) -> ToolLibrary:
        return AllTools(tool_context, spawner, agent_types, self._intents)
