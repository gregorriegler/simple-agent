from simple_agent.application.llm import ChatMessages


def to_text_messages(messages: ChatMessages) -> ChatMessages:
    """
    Flatten structured tool turns into plain {role, content} text messages.

    Adapters that speak the emoji text protocol call this so a tool result
    becomes 'Result of ...' user text and an assistant turn drops its
    structured tool_calls (the calls already live in its text content).
    """
    return [_text_message(message) for message in messages]


def _text_message(message: dict) -> dict:
    role = message.get("role", "")
    content = message.get("content", "")
    if role == "tool":
        return {"role": "user", "content": f"Result of {message['call']}\n{content}"}
    return {"role": role, "content": content}
