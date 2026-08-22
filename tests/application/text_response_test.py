from simple_agent.application.text_response import emoji_response


def test_extracts_tool_calls_and_message_keeping_raw_content():
    content = "🐙 running it 🛠️[bash echo hi /]"

    response = emoji_response(content, "m", None)

    assert response.answer == content
    assert response.message == "🐙 running it"
    assert [(c.name, c.arguments) for c in response.tool_calls] == [("bash", "echo hi")]


def test_plain_text_has_no_tool_calls():
    response = emoji_response("just talking", "m", None)

    assert response.tool_calls == []
    assert response.message == "just talking"
