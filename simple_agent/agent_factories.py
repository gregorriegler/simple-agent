from typing import Callable, Any
from simple_agent.application.agent import Agent
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM
from simple_agent.application.session_storage import SessionStorage
from simple_agent.system_prompt_generator import generate_system_prompt


def create_default_agent_factory(
    llm: LLM,
    event_bus: EventBus,
    create_subagent_display: Callable[[str, int], Any],
    create_subagent_input: Callable[[int], Input],
    agent_factory_registry
):
    def factory(
        parent_agent_id: str,
        indent_level: int,
        user_input: Input,
        session_storage: SessionStorage,
        tool_keys=[
            'write_todos',
            'ls',
            'cat',
            'create_file',
            'edit_file',
            'complete_task',
            'bash',
            'subagent'
        ]
    ) -> Agent:
        from simple_agent.tools.all_tools import AllTools

        agent_id = f"{parent_agent_id}/Subagent{indent_level}"
        subagent_tools = AllTools(
            llm,
            indent_level,
            agent_id,
            event_bus,
            user_input,
            create_subagent_display,
            create_subagent_input,
            agent_factory_registry,
            tool_keys
        )
        return Agent(
            agent_id,
            lambda tool_library: generate_system_prompt(subagent_tools),
            subagent_tools,
            llm,
            user_input,
            event_bus,
            session_storage
        )

    return factory
