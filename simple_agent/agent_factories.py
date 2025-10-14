from typing import Callable, Any
from simple_agent.application.agent import Agent
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM
from simple_agent.application.session_storage import SessionStorage
from simple_agent.system_prompt_generator import generate_system_prompt, extract_tool_keys_from_prompt


def create_default_agent_factory(
    llm: LLM,
    event_bus: EventBus,
    create_subagent_display: Callable[[str, int], Any],
    create_subagent_input: Callable[[int], Input]
):
    def factory(
        agent_type: str,
        parent_agent_id: str,
        indent_level: int,
        user_input: Input
    ) -> Agent:
        from simple_agent.tools.all_tools import AllTools
        system_prompt_file = f'{agent_type}.agent.md'
        tool_keys = extract_tool_keys_from_prompt(system_prompt_file)

        agent_id = f"{parent_agent_id}/Subagent{indent_level}"
        subagent_tools = AllTools(
            llm,
            indent_level,
            agent_id,
            event_bus,
            user_input,
            create_subagent_display,
            create_subagent_input,
            factory,
            tool_keys
        )
        from simple_agent.application.session_storage import NoOpSessionStorage
        return Agent(
            agent_id,
            lambda tool_library: generate_system_prompt(system_prompt_file, subagent_tools),
            subagent_tools,
            llm,
            user_input,
            event_bus,
            NoOpSessionStorage()
        )

    return factory
