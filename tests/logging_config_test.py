import logging

from simple_agent.logging_config import PackageLogLevelFilter, setup_logging


def _record(name: str, level: int) -> logging.LogRecord:
    return logging.LogRecord(name, level, "test.py", 1, "msg", (), None)


def test_filter_uses_base_level_for_other_packages():
    log_filter = PackageLogLevelFilter(logging.INFO, {"simple_agent": logging.DEBUG})
    assert log_filter.filter(_record("markdown_it", logging.DEBUG)) is False
    assert log_filter.filter(_record("markdown_it", logging.INFO)) is True


def test_filter_allows_debug_for_configured_package():
    log_filter = PackageLogLevelFilter(logging.INFO, {"simple_agent": logging.DEBUG})
    assert log_filter.filter(_record("simple_agent", logging.DEBUG)) is True
    assert log_filter.filter(_record("simple_agent.tools", logging.DEBUG)) is True


def test_filter_uses_more_specific_package_level():
    log_filter = PackageLogLevelFilter(
        logging.INFO,
        {"simple_agent": logging.DEBUG, "simple_agent.tools": logging.ERROR}
    )
    assert log_filter.filter(_record("simple_agent.tools", logging.WARNING)) is False
    assert log_filter.filter(_record("simple_agent.tools", logging.ERROR)) is True
    assert log_filter.filter(_record("simple_agent.agent", logging.DEBUG)) is True


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
