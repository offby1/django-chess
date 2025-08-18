#!/bin/bash

set -euxo pipefail

cd /chess

export PYTHONUNBUFFERED=t       # https://github.com/django/daphne/pull/520

exec uv run daphne                              \
    --bind 0.0.0.0                              \
    --port 8000                                 \
    --proxy-headers                             \
    --verbosity  0                              \
    django_chess.asgi:application
