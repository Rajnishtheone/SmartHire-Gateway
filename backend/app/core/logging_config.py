from __future__ import annotations

import logging
import logging.config
import sys
from typing import Any


def configure_logging(level: str = "INFO") -> None:
    """
    Configure application logging with a structured JSON formatter.

    The configuration is idempotent to avoid overriding changes made by
    test suites.
    """

    if getattr(configure_logging, "_configured", False):  # type: ignore[attr-defined]
        return

    log_config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": (
                    '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
                    '"message":"%(message)s","module":"%(module)s","line":%(lineno)d}'
                ),
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "stream": sys.stdout,
                "formatter": "json",
            }
        },
        "loggers": {
            "smarthire": {"handlers": ["console"], "level": level, "propagate": False},
            "smarthire.app": {"handlers": ["console"], "level": level, "propagate": False},
        },
        "root": {"handlers": ["console"], "level": level},
    }

    logging.config.dictConfig(log_config)
    configure_logging._configured = True  # type: ignore[attr-defined]
