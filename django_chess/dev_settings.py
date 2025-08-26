from typing import Any

from django_chess.base_settings import *  # noqa

LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": [
            "console",
        ],
        "level": "DEBUG",
    },
}
