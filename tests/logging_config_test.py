import logging

from simple_agent.infrastructure.user_configuration import UserConfiguration
from simple_agent.logging_config import setup_logging


def test_setup_logging_uses_utf8_file_handler(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    setup_logging(level="DEBUG")

    file_handlers = [
        handler
        for handler in logging.getLogger().handlers
        if isinstance(handler, logging.FileHandler)
    ]
    assert file_handlers
    assert (file_handlers[0].encoding or "").lower() == "utf-8"


def test_setup_logging_applies_logger_levels(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))

    config = {
        "log": {
            "level": "INFO",
            "loggers": {"simple_agent": "DEBUG", "simple_agent.tools": "ERROR"},
        }
    }
    user_config = UserConfiguration(config)

    setup_logging(level=None, user_config=user_config)

    assert logging.getLogger().level == logging.INFO
    assert logging.getLogger("simple_agent").level == logging.DEBUG
    assert logging.getLogger("simple_agent.tools").level == logging.ERROR
