from typing import Callable

from simple_agent.application.agent import Agent
from simple_agent.application.display import Display
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM, Messages
from simple_agent.application.subagent_context import SubagentContext
from simple_agent.application.tool_documentation import generate_tools_documentation
from simple_agent.application.tool_library_factory import ToolLibraryFactory
from simple_agent.application.agent_library import AgentLibrary


class AgentFactory:
    def __init__(
        self,
        llm: LLM,
        event_bus: EventBus,
        create_subagent_display: Callable[[str, int], Display],
        create_subagent_input: Callable[[int], Input],
        session_storage,
        tool_library_factory: ToolLibraryFactory,
        agent_library: AgentLibrary
    ):
        self.llm = llm
        self.event_bus = event_bus
        self.create_subagent_display = create_subagent_display
        self.create_subagent_input = create_subagent_input
        self.session_storage = session_storage
        self.tool_library_factory = tool_library_factory
        self.agent_library = agent_library
        self._agent_instance_counts: dict[tuple[str, str], int] = {}

    def __call__(
        self,
        agent_type: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input,
        context: Messages
    ) -> Agent:
        agent_prompt = self.agent_library.read_agent_definition(agent_type).load_prompt()
        agent_name = agent_prompt.name
        base_agent_id = f"{parent_agent_id}/{agent_name}"
        count = self._agent_instance_counts.get(base_agent_id, 0) + 1
        self._agent_instance_counts[base_agent_id] = count
        suffix = "" if count == 1 else f"-{count}"
        agent_id = f"{base_agent_id}{suffix}"

        subagent_context = SubagentContext(
            self,
            self.create_subagent_display,
            self.create_subagent_input,
            indent_level + 1,
            agent_id,
            self.event_bus
        )

        subagent_tools = self.tool_library_factory.create(agent_prompt.tool_keys, subagent_context)
        tools_documentation = generate_tools_documentation(subagent_tools.tools, self.agent_library.list_agent_types())
        system_prompt = agent_prompt.render(tools_documentation)

        context.seed_system_prompt(system_prompt)

        return Agent(
            agent_id,
            agent_name,
            subagent_tools,
            self.llm,
            user_input,
            self.event_bus,
            self.session_storage,
            context
        )
