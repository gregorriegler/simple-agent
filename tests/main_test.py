from simple_agent.application.session import SessionArgs
from simple_agent.infrastructure.configuration import stub_user_config
from simple_agent.main import parse_args, print_system_prompt_command


def test_parse_args_returns_joined_message():
    result = parse_args(["hello", "world"])

    assert result.continue_session is False
    assert result.start_message == "hello world"


def test_parse_args_sets_continue_flag_without_message():
    result = parse_args(["--continue"])

    assert result.continue_session is True
    assert result.start_message is None


def test_print_system_prompt_command_outputs_prompt(capsys, tmp_path):
    args = SessionArgs()
    user_config = stub_user_config()

    result = print_system_prompt_command(user_config, str(tmp_path), args)

    assert result is None
    assert "You are an orchestrator" in capsys.readouterr().out
