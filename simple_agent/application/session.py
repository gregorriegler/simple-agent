from dataclasses import dataclass

from simple_agent.application.agent import Agent
from simple_agent.application.llm import Messages
from simple_agent.application.persisted_messages import PersistedMessages
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.system_prompt_generator import SystemPrompt
from simple_agent.application.events import SessionStartedEvent, EventType
from simple_agent.application.display_type import DisplayType
from simple_agent.tools import AllTools


@dataclass
class SessionArgs:
    continue_session: bool
    start_message: str | None
    show_system_prompt: bool = False
    display_type: DisplayType = DisplayType.TEXTUAL


def run_session(
    continue_session: bool,
    user_input,
    session_storage: SessionStorage,
    llm,
    system_prompt: SystemPrompt,
    event_bus,
    display_event_handler=None,
    tool_library=None
):
    agent_id = "Agent"
    event_bus.publish(EventType.SESSION_STARTED, SessionStartedEvent(agent_id, continue_session))

    if tool_library is None:
        tool_library = AllTools(llm, agent_id, event_bus, display_event_handler)

    agent = Agent(
        agent_id,
        system_prompt,
        tool_library,
        llm,
        user_input,
        event_bus,
        session_storage
    )

    messages = session_storage.load() if continue_session else Messages()
    persisted_messages = PersistedMessages(messages, session_storage)
    agent.start(persisted_messages)
