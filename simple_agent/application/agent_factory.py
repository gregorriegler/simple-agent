from typing import Callable, Protocol

from simple_agent.application.agent import Agent
from simple_agent.application.display import Display
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM
from simple_agent.application.system_prompt import AgentPrompt
from simple_agent.application.tool_documentation import AgentTypeDiscovery, generate_tools_documentation
from simple_agent.application.tool_library_factory import ToolLibraryFactory


class CreateAgent(Protocol):
    create_subagent_display: Callable[[str, int], Display]
    create_subagent_input: Callable[[int], Input]

    def __call__(
        self,
        agent_type: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input
    ) -> Agent:
        ...


class AgentFactory(CreateAgent):
    def __init__(
        self,
        llm: LLM,
        event_bus: EventBus,
        create_subagent_display: Callable[[str, int], Display],
        create_subagent_input: Callable[[int], Input],
        load_agent_prompt: Callable[[str], AgentPrompt],
        session_storage,
        tool_library_factory: ToolLibraryFactory,
        agent_type_discovery: AgentTypeDiscovery
    ):
        self.llm = llm
        self.event_bus = event_bus
        self.create_subagent_display = create_subagent_display
        self.create_subagent_input = create_subagent_input
        self.load_agent_prompt = load_agent_prompt
        self.session_storage = session_storage
        self.tool_library_factory = tool_library_factory
        self.agent_type_discovery = agent_type_discovery

    def __call__(
        self,
        agent_type: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input
    ) -> Agent:
        from simple_agent.application.subagent_context import SubagentContext

        agent_prompt = self.load_agent_prompt(agent_type)
        agent_id = f"{parent_agent_id}/Subagent{indent_level + 1}"

        subagent_context = SubagentContext(
            self,
            indent_level + 1,
            agent_id
        )

        subagent_tools = self.tool_library_factory.create(agent_prompt.tool_keys, subagent_context)
        tools_documentation = generate_tools_documentation(subagent_tools.tools, self.agent_type_discovery)
        system_prompt = agent_prompt.render(tools_documentation)

        return Agent(
            agent_id,
            system_prompt,
            subagent_tools,
            self.llm,
            user_input,
            self.event_bus,
            self.session_storage
        )
