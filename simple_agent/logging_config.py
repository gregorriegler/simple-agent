import logging
import logging.config
import os
from collections.abc import Mapping
from pathlib import Path


def setup_logging(
    level: str | None = None, user_config=None, log_file: Path | None = None
) -> None:
    if level is None:
        if user_config:
            level = user_config.log_level()
        else:
            level = os.environ.get("SIMPLE_AGENT_LOG_LEVEL", "INFO").upper()
    if not level:
        level = os.environ.get("SIMPLE_AGENT_LOG_LEVEL", "INFO").upper()

    logger_level_names: Mapping[str, str] = {}
    if user_config:
        logger_level_names = user_config.logger_levels()

    if log_file is None:
        log_dir = Path.home() / ".simple-agent" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "simple-agent.log"
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(
        _build_logging_config(level, logger_level_names, log_file)
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _build_logging_config(
    base_level: str,
    logger_levels: Mapping[str, str],
    log_file: Path,
) -> dict:
    loggers = {
        logger: {"level": level, "handlers": [], "propagate": True}
        for logger, level in logger_levels.items()
    }
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": str(log_file),
                "encoding": "utf-8",
            }
        },
        "root": {"level": base_level, "handlers": ["file"]},
        "loggers": loggers,
    }
