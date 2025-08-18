FROM python:3.13-slim-bullseye AS python
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV PYTHONUNBUFFERED=t

RUN adduser --disabled-password chess

COPY uv.lock pyproject.toml manage.py start-daphne.sh /chess/
COPY django_chess/ /chess/django_chess/

WORKDIR /chess
RUN chown -R chess:chess /chess

USER chess
RUN ["uv", "sync"]

RUN ["uv", "run", "python", "manage.py", "makemigrations"]
RUN ["uv", "run", "python", "manage.py", "migrate"]
# TODO -- ensure DEBUG is False
CMD ["bash", "./start-daphne.sh"]
