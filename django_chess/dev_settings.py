from typing import Any

from django_chess.base_settings import *  # noqa
from django_chess.base_settings import INSTALLED_APPS, MIDDLEWARE

INSTALLED_APPS = ["debug_toolbar"] + INSTALLED_APPS
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

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
