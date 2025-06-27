# bibliofabric/log_config.py
"""Logging configuration for the bibliofabric library using Loguru.

This module provides a centralized function to configure the Loguru logger
with a standardized format, level, and sink for consistent logging across
the bibliofabric framework and its derived API clients.
"""

import sys

from loguru import logger


def configure_logging(level: str = "INFO", sink=sys.stderr):
    """
    Configures Loguru logger.

    Removes default handlers and adds a new one with the specified level and sink.

    Args:
        level: The minimum logging level (e.g., "DEBUG", "INFO", "WARNING").
        sink: The output sink (e.g., sys.stderr, "file.log").
    """
    logger.remove()  # Remove default handler
    logger.add(
        sink,
        level=level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=sink is sys.stderr,  # Only colorize if writing to stderr
        backtrace=True,
        diagnose=True,
    )
    logger.info(
        f"Loguru logger configured with level={level.upper()} writing to {sink}"
    )


# Example Usage:
# from .log_config import configure_logging
# configure_logging(level="DEBUG")
# logger.debug("This is a debug message.")
