import logging
import os
from pathlib import Path
from typing import Iterable, Mapping, Optional, Tuple


def setup_logging(level: Optional[str] = None, user_config = None) -> None:
    if level is None:
        if user_config:
            level = user_config.log_level()
        else:
            level = os.environ.get('SIMPLE_AGENT_LOG_LEVEL', 'INFO').upper()

    numeric_level = getattr(logging, level, logging.INFO)
    package_level_names: Mapping[str, str] = {}
    if user_config:
        package_level_names = user_config.package_log_levels()
    package_levels = _parse_package_levels(package_level_names)

    log_dir = Path.home() / '.simple-agent' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'simple-agent.log'

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(PackageLogLevelFilter(numeric_level, package_levels))

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)

    if package_levels:
        _apply_package_log_levels(package_levels)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _apply_package_log_levels(package_levels: Mapping[str, int]) -> None:
    for package, level in package_levels.items():
        logger = logging.getLogger(package)
        logger.setLevel(level)

def _parse_package_levels(package_level_names: Mapping[str, str]) -> dict[str, int]:
    return {
        package: getattr(logging, level, logging.INFO)
        for package, level in package_level_names.items()
    }


class PackageLogLevelFilter(logging.Filter):
    def __init__(self, base_level: int, package_levels: Mapping[str, int]) -> None:
        super().__init__()
        self._base_level = base_level
        self._package_levels = _sort_package_levels(package_levels)

    def filter(self, record: logging.LogRecord) -> bool:
        effective_level = self._effective_level(record.name)
        return record.levelno >= effective_level

    def _effective_level(self, logger_name: str) -> int:
        for package, level in self._package_levels:
            if logger_name == package or logger_name.startswith(f"{package}."):
                return level
        return self._base_level


def _sort_package_levels(package_levels: Mapping[str, int]) -> Iterable[Tuple[str, int]]:
    return sorted(
        package_levels.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )


def set_log_level(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger('simple_agent')
    logger.setLevel(numeric_level)
    for handler in logger.handlers:
        handler.setLevel(numeric_level)
