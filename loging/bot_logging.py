# loging/bot_logging.py
import logging
import logging.config
from .base_logging import LogConfig


def setup_bot_logging() -> logging.Logger:
    """Setup logging pentru Telegram bot."""
    config = LogConfig.get_config("bot", "bot_std.log")

    # Adaugă configurări specifice pentru bot
    config["loggers"].update({
        "telegram.ext": {
            "level": "INFO",
            "handlers": ["console", "bot_file"],
            "propagate": False
        },
        "bot.handlers": {
            "level": "DEBUG",
            "handlers": ["console", "bot_file"],
            "propagate": False
        }
    })

    logging.config.dictConfig(config)

    logger = logging.getLogger("bot")
    logger.info(">>> Bot Logging Started <<<")
    logger.info(f"Log files: bot_std.log & bot.log")

    return logger