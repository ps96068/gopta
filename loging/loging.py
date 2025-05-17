import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging() -> logging.Logger:
    """
    Sets up logging for the application.
    """
    log_directory = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_file_path = os.path.join(log_directory, "std.log")

    log_format = (
        '[%(filename)s:%(lineno)d] - [#%(levelname)-8s] - '
        '[%(asctime)s] - [%(name)s] - Message=[%(message)s]'
    )

    formatter = logging.Formatter(log_format)

    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=512000, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])

    logger = logging.getLogger(__name__)
    logger.info("Logging is set up to file and console.")

    return logger


