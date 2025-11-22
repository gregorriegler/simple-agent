from simple_agent.application.agent import Agent
from simple_agent.application.agent_id import AgentId
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
        self._agent_instance_counts: dict[tuple[str, str], int] = {}

    def __call__(
        self,
        agent_type: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input,
        context: Messages
    ) -> Agent:
        agent_prompt = self._context.agent_library.read_agent_definition(agent_type).load_prompt()
        agent_name = agent_prompt.agent_name
        base_agent_id = f"{parent_agent_id}/{agent_name}"
        count = self._agent_instance_counts.get(base_agent_id, 0) + 1
        self._agent_instance_counts[base_agent_id] = count
        suffix = "" if count == 1 else f"-{count}"
        agent_id = f"{base_agent_id}{suffix}"

        subagent_context = SubagentContext(
            self,
            self._context.create_subagent_input,
            indent_level + 1,
            AgentId(agent_id),
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
