import pytest
from unittest.mock import patch
from simple_agent.application.session import SessionArgs
from simple_agent.infrastructure.user_configuration import (
    UserConfiguration,
    ConfigurationError,
)
from simple_agent.main import parse_args, print_system_prompt_command, main


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
    user_config = UserConfiguration.create_stub()

    result = print_system_prompt_command(user_config, str(tmp_path), args)

    assert result is None
    assert "You are an orchestrator" in capsys.readouterr().out


def test_main_handles_configuration_error_gracefully(capsys):
    with patch(
        "simple_agent.main._run_main", side_effect=ConfigurationError("Missing API key")
    ):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "Configuration error: Missing API key" in captured.err
