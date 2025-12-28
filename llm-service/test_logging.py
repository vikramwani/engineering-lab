#!/usr/bin/env python3
"""
Simple script to test the logging configuration.
"""

import sys
sys.path.insert(0, 'src')

from src.config import load_settings
from src.logging_config import setup_logging
import logging

def test_logging():
    """Test the logging configuration."""
    # Load settings
    settings = load_settings()
    
    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        log_to_console=settings.log_to_console
    )
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Test different log levels
    logger.debug("This is a DEBUG message", extra={"test": "debug_level"})
    logger.info("This is an INFO message", extra={"test": "info_level"})
    logger.warning("This is a WARNING message", extra={"test": "warning_level"})
    logger.error("This is an ERROR message", extra={"test": "error_level"})
    
    print(f"✅ Logging test completed!")
    print(f"   Log Level: {settings.log_level}")
    print(f"   Log File: {settings.log_file}")
    print(f"   Console: {settings.log_to_console}")
    print(f"   Check the log file for JSON formatted output.")

if __name__ == "__main__":
    test_logging()