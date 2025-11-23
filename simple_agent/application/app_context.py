from dataclasses import dataclass
from typing import Callable

from simple_agent.application.agent_library import AgentLibrary
from simple_agent.application.event_bus_protocol import EventBus
from simple_agent.application.input import Input
from simple_agent.application.llm import LLM
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.tool_library_factory import ToolLibraryFactory


@dataclass
class AppContext:
    llm: LLM
    event_bus: EventBus
    session_storage: SessionStorage
    tool_library_factory: ToolLibraryFactory
    agent_library: AgentLibrary
    create_subagent_input: Callable[[], Input]
