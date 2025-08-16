uv-install:
    uv sync

mypy: uv-install
    uv run dmypy run -- --strict .

main: mypy
    uv run python main.py

runme: mypy
    uv run python manage.py makemigrations
    uv run python manage.py migrate
    uv run python manage.py runserver
