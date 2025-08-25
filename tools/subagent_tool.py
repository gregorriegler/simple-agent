from agent import Display
from chat import Chat

from .base_tool import BaseTool


class SubagentDisplay(Display):

    def assistant_says(self, message):
        print(f">>Assistant: {message}")

    def tool_result(self, result):
        print(f">>Tool Result: {result}")

    def input(self):
        return input("\n>>Press Enter to continue or type a message to add: ")

    def tool_about_to_execute(self, parsed_tool):
        print(f"\n>>Executing {parsed_tool}")

    def exit(self):
        print(">>Subagent completed.")


class SubagentTool(BaseTool):
    name = 'subagent'
    description = "Create a subagent to handle a specific task using the same agent architecture"
    arguments = [
        {
            "name": "task_description",
            "type": "string",
            "required": True,
            "description": "Detailed description of the task for the subagent to perform"
        }
    ]
    examples = [
        "/subagent Write a Python function to calculate fibonacci numbers",
        "/subagent Create a simple HTML page with a form"
    ]

    def __init__(self, runcommand, message_claude):
        super().__init__()
        self.runcommand = runcommand
        self.message_claude = message_claude

    def execute(self, args):
        if not args or not args.strip():
            return {
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
                'output': f"Subagent Task: {args}\n\n{output}"
            }

        except Exception as e:
            return {
                'output': f'STDERR: subagent error: {str(e)}'
            }

