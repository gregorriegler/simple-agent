from dataclasses import dataclass

from simple_agent.application.agent import Agent
from simple_agent.application.llm import Messages
from simple_agent.application.persisted_messages import PersistedMessages
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.system_prompt_generator import SystemPrompt
from simple_agent.application.events import SessionStartedEvent, EventType
from simple_agent.tools import AllTools


@dataclass
class SessionArgs:
    continue_session: bool
    start_message: str | None
    show_system_prompt: bool = False


def run_session(
    continue_session: bool,
    user_input,
    session_storage: SessionStorage,
    chat,
    system_prompt: SystemPrompt,
    event_bus,
    display_handler=None,
    tool_library=None
):
    messages = session_storage.load() if continue_session else Messages()
    persisted_messages = PersistedMessages(messages, session_storage)

    agent_id = "Agent"
    event_bus.publish(EventType.SESSION_STARTED, SessionStartedEvent(agent_id, continue_session))

    if tool_library is None:
        tool_library = AllTools(chat, agent_id=agent_id, event_bus=event_bus, display_handler=display_handler)
    agent = Agent(agent_id, chat, system_prompt, user_input, tool_library, event_bus, session_storage)
    agent.start(persisted_messages)
