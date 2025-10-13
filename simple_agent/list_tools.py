#!/usr/bin/env python
import sys
from simple_agent.application.input import Input
from simple_agent.infrastructure.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.tools import AllTools
from simple_agent.tools.all_tools import SubagentConsoleDisplay

def get_tool_info(self, tools, tool_name=None):
    if tool_name:
        tool = tools.tool_dict.get(tool_name)
        if not tool:
            return f"Tool '{tool_name}' not found. Available tools: {', '.join(self.tool_dict.keys())}"
        if hasattr(tool, 'get_usage_info'):
            return tool.get_usage_info()
        else:
            return f"Tool: {tool.name}\nDescription: {getattr(tool, 'description', 'No description available')}"
    else:
        info_lines = ["Available Tools:"]
        for tool in tools.tools:
            description = getattr(tool, 'description', 'No description available')
            info_lines.append(f"  {tool.name}: {description}")
        return "\n".join(info_lines)

if __name__ == "__main__":
    io = StdIO()
    create_subagent_display = lambda agent_id, indent: SubagentConsoleDisplay(indent, io)
    create_subagent_input = lambda indent: Input(ConsoleUserInput(indent, io))
    tools = AllTools(
        create_subagent_display=create_subagent_display,
        create_subagent_input=create_subagent_input
    )
    try:
        if len(sys.argv) > 1:
            tool_name = sys.argv[1]
            output = get_tool_info(tools, tool_name)
        else:
            output = get_tool_info(tools)
        print(output)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
