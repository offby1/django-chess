uv-install:
    uv sync

mypy: uv-install
    uv run dmypy run -- --strict .

runme: mypy
    uv run python manage.py makemigrations
    uv run python manage.py migrate
    uv run python manage.py runserver
