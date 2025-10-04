from dataclasses import dataclass

from simple_agent.application.agent import Agent
from simple_agent.application.llm import Messages
from simple_agent.application.persisted_messages import PersistedMessages
from simple_agent.application.session_storage import SessionStorage
from simple_agent.application.system_prompt import SystemPrompt
from simple_agent.tools import ToolLibrary


@dataclass
class SessionArgs:
    continue_session: bool
    start_message: str | None
    show_system_prompt: bool = False


def run_session(
    continue_session: bool,
    user_input,
    display,
    session_storage: SessionStorage,
    chat,
    system_prompt: SystemPrompt
):
    messages = session_storage.load() if continue_session else Messages()
    persisted_messages = PersistedMessages(messages, session_storage)

    if continue_session:
        display.continue_session()
    else:
        display.start_new_session()
    tool_library = ToolLibrary(chat)
    system_prompt = system_prompt()
    agent = Agent(chat, system_prompt, user_input, tool_library, display, session_storage)
    agent.start(persisted_messages)
