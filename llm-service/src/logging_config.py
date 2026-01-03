"""Structured JSON logging configuration for the LLM service.

This module sets up comprehensive logging with JSON formatting, file rotation,
and configurable log levels to support production monitoring and debugging
requirements.
"""

import logging
import logging.handlers
import os
from pathlib import Path

from pythonjsonlogger import jsonlogger


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/llm_service.log",
    log_to_console: bool = True,
):
    """Configure structured JSON logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
        log_to_console: Whether to also log to console
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Clear existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Create JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)
    root_logger.addHandler(file_handler)

    # Console handler (optional)
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(numeric_level)
        root_logger.addHandler(console_handler)

    # Log the logging configuration
    logger = logging.getLogger(__name__)
    logger.info(
        "logging_configured",
        extra={
            "log_level": log_level,
            "log_file": log_file,
            "log_to_console": log_to_console,
            "file_exists": os.path.exists(log_file),
            "handlers_count": len(root_logger.handlers),
        },
    )
