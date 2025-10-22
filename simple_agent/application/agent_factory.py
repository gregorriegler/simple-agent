from typing import Callable, Any, Protocol

from simple_agent.application.agent import Agent
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM
from simple_agent.system_prompt_generator import generate_system_prompt, extract_tool_keys_from_file


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
        session_storage
    ):
        self.llm = llm
        self.event_bus = event_bus
        self.create_subagent_display = create_subagent_display
        self.create_subagent_input = create_subagent_input
        self.session_storage = session_storage

    def __call__(
        self,
        agent_type: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input
    ) -> Agent:
        from simple_agent.tools.all_tools import AllTools
        system_prompt_file = f'{agent_type}.agent.md'
        tool_keys = extract_tool_keys_from_file(system_prompt_file)
        agent_id = f"{parent_agent_id}/Subagent{indent_level}"

        subagent_tools = AllTools(
            self.llm,
            indent_level,
            agent_id,
            self.event_bus,
            user_input,
            self.create_subagent_display,
            self.create_subagent_input,
            self,
            tool_keys
        )
        return Agent(
            agent_id,
            lambda tool_library: generate_system_prompt(system_prompt_file, tool_library),
            subagent_tools,
            self.llm,
            user_input,
            self.event_bus,
            self.session_storage
        )
