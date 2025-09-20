from dataclasses import dataclass

from application.agent import Agent
from application.chat import Messages
from application.persisted_messages import PersistedMessages
from application.session_storage import SessionStorage
from application.system_prompt import SystemPrompt
from tools import ToolLibrary


@dataclass
class SessionArgs:
    continue_session: bool
    start_message: str | None


def run_session(
    args: SessionArgs,
    user_input,
    display,
    session_storage: SessionStorage,
    chat,
    system_prompt: SystemPrompt,
    rounds=9999999
):
    messages = session_storage.load() if args.continue_session else Messages()
    persisted_messages = PersistedMessages(messages, session_storage)

    if args.continue_session:
        display.continue_session()
    else:
        display.start_new_session()
    tool_library = ToolLibrary(chat)
    system_prompt = system_prompt()
    agent = Agent(chat, system_prompt, user_input, tool_library, display, session_storage)
    agent.start(persisted_messages, rounds)
