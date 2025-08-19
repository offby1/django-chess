set unstable

export COMPOSE_PROFILE := if env("DOCKER_CONTEXT", "") == "chess" { "prod" } else { "" }
DJANGO_SECRET_DIRECTORY := config_directory() / "info.offby1.chess"
export DJANGO_SECRET_FILE := DJANGO_SECRET_DIRECTORY / "django_secret_key"
export DJANGO_SETTINGS_MODULE := env("DJANGO_SETTINGS_MODULE", "django_chess.dev_settings")

uv-install:
    uv sync

mypy: uv-install
    uv run dmypy run -- --strict .

main: mypy
    uv run python main.py

test: mypy
    uv run pytest .

runme: test
    uv run python manage.py makemigrations
    uv run python manage.py migrate
    uv run python manage.py runserver

[private]
[script('bash')]
ensure-django-secret:
    set -euo pipefail

    mkdir -vp "{{ DJANGO_SECRET_DIRECTORY }}"
    touch "{{ DJANGO_SECRET_FILE }}"
    if [ ! -f "{{ DJANGO_SECRET_FILE }}" -o $(gstat --format=%s "{{ DJANGO_SECRET_FILE }}") -lt 50 ]
    then
    uv run python  -c 'import secrets; print(secrets.token_urlsafe(100))' > "{{ DJANGO_SECRET_FILE }}"
    fi

[script('bash')]
dcu: test ensure-django-secret
    set -euo pipefail

    export CADDY_HOSTNAME=chess.offby1.info
    export DJANGO_SECRET_KEY=$(cat "${DJANGO_SECRET_FILE}")
    export GIT_VERSION=TODO

    echo COMPOSE_PROFILE is {{ COMPOSE_PROFILE }}

    docker compose                up --build --detach
    docker compose logs django --follow

prod:
    export DJANGO_SETTINGS_MODULE=django_chess.prod_settings
    DOCKER_CONTEXT=chess just dcu
