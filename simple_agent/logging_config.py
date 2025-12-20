import logging
import os
from pathlib import Path
from typing import Optional


def setup_logging(level: Optional[str] = None, user_config = None) -> None:
    if level is None:
        if user_config:
            level = user_config.log_level()
        else:
            level = os.environ.get('SIMPLE_AGENT_LOG_LEVEL', 'INFO').upper()

    numeric_level = getattr(logging, level, logging.INFO)

    log_dir = Path.home() / '.simple-agent' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'simple-agent.log'

    logger = logging.getLogger('simple_agent')
    logger.setLevel(numeric_level)

    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(numeric_level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger('simple_agent')
    logger.setLevel(numeric_level)
    for handler in logger.handlers:
        handler.setLevel(numeric_level)
