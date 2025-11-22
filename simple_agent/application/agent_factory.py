from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId, AgentIdSuffixer
from simple_agent.application.agent_type import AgentType
from simple_agent.application.app_context import AppContext
from simple_agent.application.input import Input
from simple_agent.application.llm import Messages
from simple_agent.application.subagent_context import SubagentContext
from simple_agent.application.tool_documentation import generate_tools_documentation


class AgentFactory:
    def __init__(
        self,
        app_context: AppContext
    ):
        self._context = app_context
        self._agent_suffixer = AgentIdSuffixer()

    def __call__(
        self,
        agent_type: AgentType,
        parent_agent_id: AgentId,
        indent_level: int,
        user_input: Input,
        context: Messages
    ) -> Agent:
        definition = self._context.agent_library.read_agent_definition(agent_type)
        agent_prompt = definition.load_prompt()
        agent_name = definition.agent_name()
        agent_id = parent_agent_id.create_subagent_id(agent_name, self._agent_suffixer)

        subagent_context = SubagentContext(
            self,
            self._context.create_subagent_input,
            indent_level + 1,
            agent_id,
            self._context.event_bus
        )

        subagent_tools = self._context.tool_library_factory.create(agent_prompt.tool_keys, subagent_context)
        tools_documentation = generate_tools_documentation(subagent_tools.tools, self._context.agent_library.list_agent_types())
        system_prompt = agent_prompt.render(tools_documentation)

        context.seed_system_prompt(system_prompt)

        return Agent(
            agent_id,
            agent_name,
            subagent_tools,
            self._context.llm,
            user_input,
            self._context.event_bus,
            self._context.session_storage,
            context
        )
