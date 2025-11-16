from simple_agent.application.subagent_context import SubagentContext
from simple_agent.application.tool_library import ToolLibrary
from simple_agent.application.tool_library_factory import ToolLibraryFactory
from simple_agent.tools.all_tools import AllTools


class AllToolsFactory(ToolLibraryFactory):
    def create(
        self,
        tool_keys: list[str],
        subagent_context: SubagentContext
    ) -> ToolLibrary:
        return AllTools(tool_keys, subagent_context)
