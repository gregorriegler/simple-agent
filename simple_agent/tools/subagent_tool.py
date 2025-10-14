from simple_agent.application.tool_library import ContinueResult
from simple_agent.application.agent_factory_registry import AgentFactoryRegistry
from simple_agent.application.session_storage import NoOpSessionStorage
from .argument_parser import split_arguments
from .base_tool import BaseTool


class SubagentTool(BaseTool):
    name = 'subagent'
    description = "Creates a new subagent that will handle a specific task/todo and report back the result."
    arguments = [
        {
            "name": "agenttype",
            "type": "string",
            "required": True,
            "description": "Type of agent to create (currently only 'default' is supported)"
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

    def __init__(
        self,
        agent_factory_registry: AgentFactoryRegistry,
        create_display,
        indent_level: int,
        parent_agent_id: str,
        create_user_input
    ):
        super().__init__()
        self.agent_factory_registry = agent_factory_registry
        self.create_display = create_display
        self.indent_level = indent_level
        self.parent_agent_id = parent_agent_id
        self.create_user_input = create_user_input

    def execute(self, args):
        if not args or not args.strip():
            return ContinueResult('STDERR: subagent: missing arguments')

        try:
            parts = split_arguments(args)
        except ValueError as exc:
            return ContinueResult(f"STDERR: subagent: {exc}")

        if len(parts) < 2:
            return ContinueResult('STDERR: subagent: missing agenttype or task description')

        agenttype = parts[0]
        task_description = ' '.join(parts[1:])

        available_types = self.agent_factory_registry.get_available_types()
        if agenttype not in available_types:
            return ContinueResult(
                f"STDERR: subagent: unsupported agenttype '{agenttype}'. "
                f"Available types: {', '.join(available_types)}"
            )

        try:
            user_input = self.create_user_input(self.indent_level)
            user_input.stack(task_description)
            create_agent = self.agent_factory_registry.get_by_type(agenttype)
            system_prompt_file = f'{agenttype}.agent.md'
            subagent = create_agent(
                system_prompt_file,
                self.parent_agent_id,
                self.indent_level,
                user_input,
                NoOpSessionStorage()
            )
            self.create_display(subagent.agent_id, self.indent_level)

            result = subagent.start()

            return ContinueResult(str(result))
        except Exception as e:
            return ContinueResult(f'STDERR: subagent error: {str(e)}')
