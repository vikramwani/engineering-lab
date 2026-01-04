"""Structured logging utilities for the agent alignment framework.

This module provides consistent logging configuration and utilities
for structured logging across the framework.
"""

import logging
import sys
from typing import Optional

try:
    from pythonjsonlogger import jsonlogger
    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_to_console: bool = True,
    use_json_format: bool = True,
) -> None:
    """Set up structured logging for the framework.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        log_to_console: Whether to log to console
        use_json_format: Whether to use JSON formatting (requires pythonjsonlogger)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if use_json_format and HAS_JSON_LOGGER:
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up file logging to {log_file}: {e}")
    
    # Log configuration
    logger = get_logger(__name__)
    logger.info(
        "logging_configured",
        extra={
            "log_level": log_level,
            "log_file": log_file,
            "log_to_console": log_to_console,
            "use_json_format": use_json_format and HAS_JSON_LOGGER,
            "handlers_count": len(root_logger.handlers),
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that ensures structured logging with extra fields.
    
    This adapter automatically includes common fields in log messages
    and provides convenience methods for structured logging.
    """
    
    def __init__(self, logger: logging.Logger, extra: Optional[dict] = None):
        """Initialize the adapter.
        
        Args:
            logger: Base logger instance
            extra: Default extra fields to include in all log messages
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """Process log message and kwargs to ensure structured format."""
        # Ensure extra dict exists
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # Merge default extra fields
        kwargs['extra'].update(self.extra)
        
        return msg, kwargs
    
    def log_agent_event(
        self,
        level: int,
        event: str,
        agent_name: str,
        task_id: str,
        **extra_fields
    ) -> None:
        """Log an agent-related event with standard fields.
        
        Args:
            level: Log level
            event: Event name
            agent_name: Name of the agent
            task_id: Task identifier
            **extra_fields: Additional fields to include
        """
        extra = {
            "event": event,
            "agent_name": agent_name,
            "task_id": task_id,
            **extra_fields
        }
        self.log(level, event, extra=extra)
    
    def log_evaluation_event(
        self,
        level: int,
        event: str,
        task_id: str,
        request_id: str,
        **extra_fields
    ) -> None:
        """Log an evaluation-related event with standard fields.
        
        Args:
            level: Log level
            event: Event name
            task_id: Task identifier
            request_id: Request identifier
            **extra_fields: Additional fields to include
        """
        extra = {
            "event": event,
            "task_id": task_id,
            "request_id": request_id,
            **extra_fields
        }
        self.log(level, event, extra=extra)


def get_structured_logger(name: str, **default_extra) -> StructuredLoggerAdapter:
    """Get a structured logger adapter with default extra fields.
    
    Args:
        name: Logger name
        **default_extra: Default extra fields to include in all messages
        
    Returns:
        StructuredLoggerAdapter: Configured structured logger
    """
    base_logger = get_logger(name)
    return StructuredLoggerAdapter(base_logger, default_extra)