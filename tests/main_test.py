from simple_agent.main import parse_args


def test_parse_args_returns_joined_message():
    result = parse_args(["hello", "world"])

    assert result.continue_session is False
    assert result.start_message == "hello world"


def test_parse_args_sets_continue_flag_without_message():
    result = parse_args(["--continue"])

    assert result.continue_session is True
    assert result.start_message is None
