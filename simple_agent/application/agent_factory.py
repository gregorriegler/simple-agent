from typing import Callable, Any, Protocol

from simple_agent.application.agent import Agent
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM
from simple_agent.application.system_prompt import AgentPrompt


class CreateAgent(Protocol):
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
        create_subagent_display: Callable[[str, int], Any],
        create_subagent_input: Callable[[int], Input],
        load_agent_prompt: Callable[[str], AgentPrompt],
        session_storage
    ):
        self.llm = llm
        self.event_bus = event_bus
        self.create_subagent_display = create_subagent_display
        self.create_subagent_input = create_subagent_input
        self.load_agent_prompt = load_agent_prompt
        self.session_storage = session_storage

    def __call__(
        self,
        agent_type: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input
    ) -> Agent:
        from simple_agent.tools.all_tools import AllTools
        prompt = self.load_agent_prompt(agent_type)
        agent_id = f"{parent_agent_id}/Subagent{indent_level}"

        subagent_tools = AllTools(
            indent_level,
            agent_id,
            self.create_subagent_display,
            self.create_subagent_input,
            self,
            prompt.tool_keys
        )
        from simple_agent.tools.tool_documentation import generate_tools_documentation

        tools_documentation = generate_tools_documentation(subagent_tools.tools)
        system_prompt = prompt.render(tools_documentation)

        return Agent(
            agent_id,
            system_prompt,
            subagent_tools,
            self.llm,
            user_input,
            self.event_bus,
            self.session_storage
        )
