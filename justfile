set unstable

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
