from django_chess.base_settings import *  # noqa
from django_chess.base_settings import INSTALLED_APPS, MIDDLEWARE

INSTALLED_APPS = ["debug_toolbar"] + INSTALLED_APPS
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
