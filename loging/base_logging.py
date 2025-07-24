# loging/base_logging.py
import os
import logging
import logging.config
from pathlib import Path
from typing import Optional


class LogConfig:
    """Configurare centralizată pentru logging."""

    LOG_DIR = Path("logs")
    LOG_FORMAT = (
        '[%(filename)s:%(lineno)d] - [#%(levelname)-8s] - '
        '[%(asctime)s] - [%(name)s] - Message=[%(message)s]'
    )

    # Nivele de logging per modul
    MODULE_LEVELS = {
        "watchfiles": logging.WARNING,
        "uvicorn.access": logging.INFO,
        "sqlalchemy.engine": logging.WARNING,
        "asyncpg": logging.WARNING,
        "fastapi": logging.INFO,
        "telegram": logging.INFO,
    }

    @classmethod
    def get_config(cls, component: str, log_file: str) -> dict:
        """Generează configurație pentru o componentă."""
        cls.LOG_DIR.mkdir(exist_ok=True)

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": cls.LOG_FORMAT
                },
                "simple": {
                    "format": "%(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": str(cls.LOG_DIR / log_file),
                    "maxBytes": 5242880,  # 5MB
                    "backupCount": 5,
                    "encoding": "utf-8"
                },
                f"{component}_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": str(cls.LOG_DIR / f"{component}.log"),
                    "maxBytes": 2097152,  # 2MB
                    "backupCount": 3,
                    "encoding": "utf-8"
                }
            },
            "loggers": {
                # Root logger
                "": {
                    "level": "INFO",
                    "handlers": ["console", "file"]
                },
                # Component-specific logger
                component: {
                    "level": "DEBUG",
                    "handlers": ["console", f"{component}_file"],
                    "propagate": False
                },
                # Silence noisy modules
                **{
                    module: {
                        "level": level,
                        "handlers": ["file"],
                        "propagate": False
                    }
                    for module, level in cls.MODULE_LEVELS.items()
                }
            }
        }