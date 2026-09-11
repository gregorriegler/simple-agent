from simple_agent.application.llm import (
    AssistantMessage,
    ChatMessages,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.tool_library import ToolCall
from simple_agent.infrastructure.claude.claude_tools import native_id


def to_messages_api(messages: ChatMessages) -> list[dict]:
    """
    Renders a conversation into Messages API messages: an assistant turn
    carries its calls as 'tool_use' blocks and the results of one turn
    answer them together in a single user message of 'tool_result'
    blocks. A call made without an id, under the emoji syntax or by
    another adapter, is replayed under a synthetic one, matched to its
    result by order.
    """
    renderer = _MessagesApiMessages()
    rendered: list[dict] = []
    for message in messages:
        wire = message.render(renderer)
        if rendered and _is_tool_results(wire) and _is_tool_results(rendered[-1]):
            rendered[-1]["content"].extend(wire["content"])
        else:
            rendered.append(wire)
    return rendered


def _is_tool_results(message: dict) -> bool:
    content = message["content"]
    return isinstance(content, list) and all(
        block["type"] == "tool_result" for block in content
    )


class _MessagesApiMessages:
    def __init__(self) -> None:
        self._call_index = 0
        self._result_index = 0

    def system(self, message: SystemMessage) -> dict:
        raise TypeError("a system prompt is not a message; split it off first")

    def user(self, message: UserMessage) -> dict:
        return {"role": "user", "content": message.content}

    def assistant(self, message: AssistantMessage) -> dict:
        if not message.tool_calls:
            return {"role": "assistant", "content": message.content}
        content: list[dict] = []
        if message.content:
            content.append({"type": "text", "text": message.content})
        for call in message.tool_calls:
            self._call_index += 1
            content.append(
                self._tool_use(native_id(call) or f"toolu_{self._call_index}", call)
            )
        return {"role": "assistant", "content": content}

    def tool_result(self, message: ToolResultMessage) -> dict:
        self._result_index += 1
        call_id = native_id(message.call) or f"toolu_{self._result_index}"
        block = {"type": "tool_result", "tool_use_id": call_id}
        if message.content:
            block["content"] = message.content
        return {"role": "user", "content": [block]}

    def _tool_use(self, call_id: str, call: ToolCall) -> dict:
        return {
            "type": "tool_use",
            "id": call_id,
            "name": call.name,
            "input": call.named_arguments,
        }
