from typing import Any

from django_chess.base_settings import *  # noqa

ALLOWED_HOSTS.extend(
    [
        "127.0.0.1",
        "10.0.2.2",  # android emulator
    ]
)


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
