import json

from simple_agent.application.llm import (
    AssistantMessage,
    ChatMessages,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.tool_library import ToolCall
from simple_agent.infrastructure.openai.openai_tools import native_id


def to_chat_completion_messages(messages: ChatMessages) -> list[dict]:
    renderer = ChatCompletionMessages()
    return [message.render(renderer) for message in messages]


class ChatCompletionMessages:
    """
    Renders a conversation into chat completion messages: an assistant
    turn carries its calls as 'tool_calls' and a tool result is a 'tool'
    message answering the call's id. A call made without an id, under the
    emoji syntax or by another adapter, is replayed under a synthetic one,
    matched to its result by order.
    """

    def __init__(self) -> None:
        self._call_index = 0
        self._result_index = 0

    def system(self, message: SystemMessage) -> dict:
        return {"role": "system", "content": message.content}

    def user(self, message: UserMessage) -> dict:
        return {"role": "user", "content": message.content}

    def assistant(self, message: AssistantMessage) -> dict:
        if not message.tool_calls:
            return {"role": "assistant", "content": message.content}
        tool_calls = []
        for call in message.tool_calls:
            self._call_index += 1
            tool_calls.append(
                self._tool_call(native_id(call) or f"call_{self._call_index}", call)
            )
        return {
            "role": "assistant",
            "content": message.content or None,
            "tool_calls": tool_calls,
        }

    def tool_result(self, message: ToolResultMessage) -> dict:
        self._result_index += 1
        call_id = native_id(message.call) or f"call_{self._result_index}"
        return {"role": "tool", "tool_call_id": call_id, "content": message.content}

    def _tool_call(self, call_id: str, call: ToolCall) -> dict:
        return {
            "id": call_id,
            "type": "function",
            "function": {
                "name": call.name,
                "arguments": json.dumps(call.named_arguments),
            },
        }
