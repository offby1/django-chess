set unstable

export COMPOSE_PROFILES := env("COMPOSE_PROFILES", if env("DOCKER_CONTEXT", "") == "chess" { "prod" } else { "" })
DJANGO_SECRET_DIRECTORY := config_directory() / "info.offby1.chess"
export DJANGO_SECRET_FILE := DJANGO_SECRET_DIRECTORY / "django_secret_key"
export DJANGO_SETTINGS_MODULE := env("DJANGO_SETTINGS_MODULE", "django_chess.dev_settings")

mypy:
    uv run dmypy run -- --strict .

demo: mypy
    uv run python main.py

manage *options:
    uv run python manage.py {{ options }}

test *options: (manage "makemigrations") (manage "migrate") mypy
    uv run pytest {{ options }} .

runme: test version-file (manage "runserver")

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

[private]
version-file:
    uv run python generate-version-html.py > django_chess/app/templates/app/version.html

[script('bash')]
dc *options: test ensure-django-secret version-file
    set -euo pipefail

    export CADDY_HOSTNAME=chess.offby1.info
    export DJANGO_SECRET_KEY=$(cat "${DJANGO_SECRET_FILE}")

    echo COMPOSE_PROFILES is {{ COMPOSE_PROFILES }}

    docker compose {{ options }}

dcu *options: (dc "up --build " + options)

[script('bash')]
prod:
    set -euo pipefail

    export DJANGO_SETTINGS_MODULE=django_chess.prod_settings
    DOCKER_CONTEXT=chess just dc up --build --detach
