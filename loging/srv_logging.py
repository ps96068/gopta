# loging/srv_logging.py
import logging
import logging.config
from .base_logging import LogConfig


def setup_srv_logging() -> logging.Logger:
    """Setup logging pentru server FastAPI."""
    config = LogConfig.get_config("server", "srv_std.log")

    # Adaugă configurări specifice pentru server
    config["loggers"].update({
        "server.dashboard": {
            "level": "DEBUG",
            "handlers": ["console", "server_file"],
            "propagate": False
        },
        "server.routers": {
            "level": "INFO",
            "handlers": ["console", "server_file"],
            "propagate": False
        },
        "services": {
            "level": "INFO",
            "handlers": ["file", "server_file"],
            "propagate": False
        }
    })

    logging.config.dictConfig(config)

    logger = logging.getLogger("server")
    logger.info(">>> Server Logging Started <<<")
    logger.info(f"Log files: srv_std.log & server.log")

    return logger