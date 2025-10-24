from simple_agent.application.tool_library import ContinueResult
from .base_tool import BaseTool
from simple_agent.application.subagent_context import SubagentContext


class SubagentTool(BaseTool):
    name = 'subagent'
    description = "Creates a new subagent that will handle a specific task/todo and report back the result."
    arguments = [
        {
            "name": "agenttype",
            "type": "string",
            "required": True,
            "description": "Type of agent to create {{AGENT_TYPES}}. The agenttype is expected to be on the same line as the toolcall"
        },
        {
            "name": "task_description",
            "type": "string",
            "required": True,
            "description": "Detailed description of the task for the subagent to perform"
        }
    ]
    examples = [
        "🛠️ subagent default Write a Python function to calculate fibonacci numbers",
        "🛠️ subagent default Create a simple HTML page with a form"
    ]

    def __init__(self, context: SubagentContext):
        super().__init__()
        self.context = context

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult('STDERR: subagent: missing arguments')

        parts = args.strip().split(None, 1)

        if len(parts) < 2:
            return ContinueResult('STDERR: subagent: missing agenttype or task description')

        agenttype = parts[0]
        task_description = parts[1]

        try:
            user_input = self.context.create_input(self.context.indent_level)
            user_input.stack(task_description)
            subagent = self.context.create_agent(
                agenttype,
                self.context.agent_id,
                self.context.indent_level,
                user_input
            )
            self.context.create_display(subagent.agent_id, subagent.agent_name, self.context.indent_level)

            result = subagent.start()

            return ContinueResult(str(result))
        except Exception as e:
            return ContinueResult(f'STDERR: subagent error: {str(e)}')
