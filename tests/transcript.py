"""How calls and messages read in a test transcript."""

from simple_agent.application.llm import (
    AssistantMessage,
    ChatMessage,
    ChatMessages,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.tool_library import describe_call


def transcript_line(message: ChatMessage) -> tuple[str, str]:
    """A message as its role and text; an assistant turn lists its calls."""
    return message.render(_AS_TRANSCRIPT)


def render_messages(messages: ChatMessages) -> str:
    lines = []
    for message in messages:
        role, text = transcript_line(message)
        lines.extend(line.rstrip() for line in f"{role}: {text}".split("\n"))
    return "\n".join(lines)


class _AsTranscript:
    def system(self, message: SystemMessage) -> tuple[str, str]:
        return "system", message.content

    def user(self, message: UserMessage) -> tuple[str, str]:
        return "user", message.content

    def assistant(self, message: AssistantMessage) -> tuple[str, str]:
        calls = "".join(f"\n  {describe_call(c)}" for c in message.tool_calls)
        return "assistant", message.content + calls

    def tool_result(self, message: ToolResultMessage) -> tuple[str, str]:
        return "tool_result", message.content


_AS_TRANSCRIPT = _AsTranscript()
