import logging
from pythonjsonlogger import jsonlogger


def setup_logging():
    """Configure structured JSON logging for the application.
    
    Sets up a StreamHandler with JSON formatting and INFO level logging.
    Clears existing handlers to prevent duplicates on reload.
    """
    handler = logging.StreamHandler()

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers on reload
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
