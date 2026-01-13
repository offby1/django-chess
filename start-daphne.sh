#!/bin/bash

set -euxo pipefail

cd /chess

export PYTHONUNBUFFERED=t       # https://github.com/django/daphne/pull/520

# Unstick any games where AI was interrupted (e.g., by deployment)
uv run --no-dev python manage.py unstick_games

exec uv run --no-dev daphne                     \
    --bind 0.0.0.0                              \
    --port 8000                                 \
    --proxy-headers                             \
    --verbosity  0                              \
    django_chess.asgi:application
