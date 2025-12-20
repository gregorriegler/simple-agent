from simple_agent.infrastructure.user_configuration import UserConfiguration


def test_logger_levels_returns_empty_dict_when_no_loggers_section():
    config = {"log": {"level": "INFO"}}
    user_config = UserConfiguration(config)
    assert user_config.logger_levels() == {}


def test_logger_levels_returns_empty_dict_when_no_log_section():
    config = {}
    user_config = UserConfiguration(config)
    assert user_config.logger_levels() == {}


def test_logger_levels_reads_from_config():
    config = {
        "log": {
            "level": "INFO",
            "loggers": {
                "simple_agent": "DEBUG",
                "simple_agent.tools": "WARNING"
            }
        }
    }
    user_config = UserConfiguration(config)
    levels = user_config.logger_levels()

    assert levels == {
        "simple_agent": "DEBUG",
        "simple_agent.tools": "WARNING"
    }


def test_logger_levels_uppercases_level_names():
    config = {
        "log": {
            "level": "info",
            "loggers": {
                "simple_agent": "debug",
                "urllib3": "warning"
            }
        }
    }
    user_config = UserConfiguration(config)
    levels = user_config.logger_levels()

    assert levels == {
        "simple_agent": "DEBUG",
        "urllib3": "WARNING"
    }
