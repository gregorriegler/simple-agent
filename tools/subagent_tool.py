# Use dynamic imports to avoid circular import issues
from chat import Chat

from .base_tool import BaseTool


class SubagentDisplay:
    """Display class that captures output instead of printing to console"""

    def __init__(self):
        self.output_buffer = []
        self.user_input_buffer = []

    def assistant_says(self, message):
        self.output_buffer.append(f">>Assistant: {message}")

    def tool_result(self, result):
        if result:
            self.output_buffer.append(f">>Tool Result: {result}")

    def input(self):
        # For subagent, we don't want interactive input, so return empty string
        # This will cause the agent to continue processing
        return ""

    def exit(self):
        self.output_buffer.append(">>Subagent completed.")


class SubagentTool(BaseTool):
    name = 'subagent'
    description = "Create a subagent to handle a specific task using the same agent architecture"

    def __init__(self, runcommand, message_claude):
        super().__init__()
        self.runcommand = runcommand
        self.message_claude = message_claude

    def execute(self, args):
        if not args or not args.strip():
            return {
                'success': False,
                'output': 'STDERR: subagent: missing task description'
            }

        try:
            # Import Agent and SystemPromptGenerator here to avoid circular dependency
            from agent import Agent
            from system_prompt_generator import SystemPromptGenerator

            system_prompt = SystemPromptGenerator().generate_system_prompt()
            subagent_display = SubagentDisplay()

            # Create a new ToolLibrary instance for the subagent to avoid recursion
            from tools.tool_library import ToolLibrary
            subagent_tools = ToolLibrary(self.message_claude)

            # Remove SubagentTool from subagent's tools to prevent infinite recursion
            subagent_tools.tools = [tool for tool in subagent_tools.tools if tool.name != 'subagent']
            subagent_tools._build_tool_dict()

            subagent = Agent(system_prompt, self.message_claude, subagent_display, subagent_tools)

            subagent_chat = Chat()
            subagent_chat.user_says(args.strip())
            subagent.start(subagent_chat, rounds=5)

            # Get the captured output from the last assistant message
            messages = subagent_chat.to_list()
            if messages:
                last_message = messages[-1]
                if last_message.get('role') == 'assistant':
                    output = last_message.get('content', 'No output generated')
                else:
                    output = 'No assistant response generated'
            else:
                output = 'No messages generated'

            return {
                'success': True,
                'output': f"Subagent Task: {args}\n\n{output}"
            }

        except Exception as e:
            return {
                'success': False,
                'output': f'STDERR: subagent error: {str(e)}'
            }

    def get_usage_info(self):
        return """Tool: subagent
Description: Create a subagent to handle a specific task using the same agent architecture

Usage: /subagent <task_description>

Examples:
  /subagent Write a Python function to calculate fibonacci numbers
  /subagent Create a simple HTML page with a form
  /subagent Explain how to implement a binary search algorithm

The subagent will:
- Use the same system prompt and tools as the main agent
- Process the task in a separate chat context
- Run for a limited number of rounds to prevent infinite loops
- Return all output captured during execution
"""
