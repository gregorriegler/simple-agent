from simple_agent.application.llm import (
    AssistantMessage,
    ChatMessage,
    SystemMessage,
    ToolResultMessage,
    UserMessage,
)
from simple_agent.application.tool_library import ToolCall, describe_call
from simple_agent.infrastructure.gemini.gemini_tools import native_id, thought_signature

EMPTY_TEXT_PLACEHOLDER = "(empty)"


class UnsignedTurnsAsText:
    """
    Gemini rejects a function_call/function_result pair that is not led
    by the thought step which produced it. Only calls Gemini made itself
    carry that signature; calls made by another adapter or before a model
    switch are replayed as plain text describing the call and its result.
    """

    def __init__(self) -> None:
        self._signed = False

    def system(self, message: SystemMessage) -> ChatMessage:
        return message

    def user(self, message: UserMessage) -> ChatMessage:
        return message

    def assistant(self, message: AssistantMessage) -> ChatMessage:
        self._signed = any(thought_signature(call) for call in message.tool_calls)
        if self._signed or not message.tool_calls:
            return message
        calls = "\n".join(self._call_text(call) for call in message.tool_calls)
        content = f"{message.content}\n{calls}" if message.content else calls
        return AssistantMessage(content)

    def tool_result(self, message: ToolResultMessage) -> ChatMessage:
        if self._signed:
            return message
        return UserMessage(
            f"Result of {describe_call(message.call)}:\n{message.content}"
        )

    def _call_text(self, call: ToolCall) -> str:
        return f"Called {describe_call(call)}"


class InteractionSteps:
    """
    Renders a conversation into Interactions API input steps: system
    messages join into the system_instruction, user messages become
    'user_input' steps, assistant messages 'model_output' steps with their
    calls, tool results 'function_result' steps.
    """

    def __init__(self) -> None:
        self._system_prompts: list[str] = []
        self.steps: list[dict] = []
        self._call_index = 0
        self._result_index = 0

    @property
    def system_instruction(self) -> str:
        return "\n\n".join(self._system_prompts)

    def system(self, message: SystemMessage) -> None:
        self._system_prompts.append(message.content)

    def user(self, message: UserMessage) -> None:
        self.steps.append(self._step("user_input", message.content))

    def assistant(self, message: AssistantMessage) -> None:
        turn = []
        if message.content or not message.tool_calls:
            turn.append(self._step("model_output", message.content))
        for call in message.tool_calls:
            self._call_index += 1
            if thought_signature(call):
                turn.append({"type": "thought", "signature": thought_signature(call)})
            turn.append(
                self._function_call_step(
                    native_id(call) or f"call_{self._call_index}", call
                )
            )
        self.steps.extend(self._thought_first(turn))

    def tool_result(self, message: ToolResultMessage) -> None:
        self._result_index += 1
        call_id = native_id(message.call) or f"call_{self._result_index}"
        self.steps.append(
            self._function_result_step(call_id, message.call, message.content)
        )

    def _thought_first(self, turn: list[dict]) -> list[dict]:
        """
        Thinking models reject a model turn that carries a thought summary
        without starting on a thought block, so lead with the first one.
        """
        for position, step in enumerate(turn):
            if step["type"] == "thought":
                return [step, *turn[:position], *turn[position + 1 :]]
        return turn

    def _step(self, step_type: str, text: str) -> dict:
        return {"type": step_type, "content": [self._text_content(text)]}

    def _text_content(self, text: str) -> dict:
        """Gemini rejects a text part that carries no text."""
        return {"type": "text", "text": text or EMPTY_TEXT_PLACEHOLDER}

    def _function_call_step(self, call_id: str, call: ToolCall) -> dict:
        return {
            "type": "function_call",
            "id": call_id,
            "name": call.name,
            "arguments": call.named_arguments,
        }

    def _function_result_step(self, call_id: str, call: ToolCall, output: str) -> dict:
        """
        Gemini 2.5 models reject a function result made of content parts
        ("Multimodal function responses are not supported"); every model
        accepts a plain string, an empty one included.
        """
        return {
            "type": "function_result",
            "call_id": call_id,
            "name": call.name,
            "result": output,
        }
