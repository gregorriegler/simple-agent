#!/usr/bin/env python
import sys
from simple_agent.application.input import Input
from simple_agent.infrastructure.console_user_input import ConsoleUserInput
from simple_agent.infrastructure.stdio import StdIO
from simple_agent.tools import AllTools
from simple_agent.tools.all_tools import SubagentConsoleDisplay

if __name__ == "__main__":
    command = ' '.join(sys.argv[1:])
    io = StdIO()
    create_subagent_display = lambda agent_id, indent: SubagentConsoleDisplay(indent, io)
    create_subagent_input = lambda indent: Input(ConsoleUserInput(indent, io))
    tools = AllTools(
        create_subagent_display=create_subagent_display,
        create_subagent_input=create_subagent_input
    )
    try:
        tool = tools.parse_message_and_tools(f"🛠️ {command}")
        if not tool:
            print(f"Unknown tool: {command}")
            sys.exit(1)
        output = tools.execute_parsed_tool(tool)
        print(output)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
