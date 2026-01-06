from simple_agent.application.llm import LLMResponse, Messages


def test_llm_response_defaults_usage():
    response = LLMResponse(content="Hello")

    assert response.usage is not None
    assert response.usage.total_tokens == 0


def test_messages_replaces_seeded_system_prompt():
    messages = Messages([{"role": "system", "content": "old"}], system_prompt="new")

    assert messages.to_list()[0]["content"] == "new"


def test_messages_clear_keeps_system_prompt():
    messages = Messages(system_prompt="system")
    messages.user_says("hello")

    messages.clear()

    assert len(messages) == 1
    assert messages.to_list()[0]["role"] == "system"


def test_messages_ignores_empty_user_message():
    messages = Messages()

    messages.user_says("")

    assert len(messages) == 0
