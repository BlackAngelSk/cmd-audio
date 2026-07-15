"""Centralized logging configuration for cmd-audio.

Usage:
    from cmd_audio.logging_config import setup_logging, get_logger
    setup_logging(verbosity=1)  # 0=WARNING, 1=INFO, 2=DEBUG
    logger = get_logger(__name__)
"""

from __future__ import annotations

import logging
import sys
from typing import Optional

# Module-level logger cache
_loggers: dict = {}

# Default format: timestamp [LEVEL] module: message
_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DEFAULT_DATE_FORMAT = "%H:%M:%S"

# Root logger name for the package
_ROOT_NAME = "cmd_audio"


def setup_logging(
    verbosity: int = 1,
    log_file: Optional[str] = None,
    format_str: Optional[str] = None,
) -> None:
    """Configure the root logger for the cmd_audio package.

    Args:
        verbosity: 0 = WARNING only, 1 = INFO (default), 2 = DEBUG, 3+ = DEBUG with extra detail
        log_file: Optional file path to also write logs to.
        format_str: Optional custom log format string.
    """
    if verbosity <= 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG

    fmt = format_str or _DEFAULT_FORMAT
    formatter = logging.Formatter(fmt, datefmt=_DEFAULT_DATE_FORMAT)

    # Configure root logger
    root = logging.getLogger(_ROOT_NAME)
    root.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root.handlers.clear()

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger for the given module name.

    If the name does not start with 'cmd_audio', it will be prefixed.
    Returns a cached logger instance.

    Args:
        name: Usually __name__ from the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    if name not in _loggers:
        if name.startswith(_ROOT_NAME + "."):
            logger_name = name
        elif name == _ROOT_NAME:
            logger_name = name
        else:
            logger_name = f"{_ROOT_NAME}.{name}"
        _loggers[name] = logging.getLogger(logger_name)
    return _loggers[name]


def set_log_level(level: int) -> None:
    """Dynamically adjust the log level.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    """
    root = logging.getLogger(_ROOT_NAME)
    root.setLevel(level)