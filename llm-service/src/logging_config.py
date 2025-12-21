import logging
from pythonjsonlogger import jsonlogger


def setup_logging():
    handler = logging.StreamHandler()

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Avoid duplicate handlers on reload
    root.handlers.clear()
    root.addHandler(handler)
