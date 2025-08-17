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
