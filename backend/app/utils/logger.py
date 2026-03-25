"""Logging helpers."""

import logging
import os
import sys
from typing import Optional


def setup_logger(name: str, level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger and ensure at least one handler is attached."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger = setup_logger(name, level=LOG_LEVEL)
    return logger


LOG_LEVEL = logging.INFO
if os.getenv("LOG_LEVEL") == "DEBUG":
    LOG_LEVEL = logging.DEBUG
elif os.getenv("LOG_LEVEL") == "WARNING":
    LOG_LEVEL = logging.WARNING
elif os.getenv("LOG_LEVEL") == "ERROR":
    LOG_LEVEL = logging.ERROR

app_logger = setup_logger("app", level=LOG_LEVEL)
