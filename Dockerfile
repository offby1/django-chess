FROM python:3.13-slim-bullseye AS python
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt -y update
RUN apt -y install git gnuchess

ENV PYTHONUNBUFFERED=t

FROM python AS uv-install-django

COPY uv.lock pyproject.toml /chess/
WORKDIR /chess
RUN ["uv", "sync", "--no-dev"]

FROM python:3.13-slim-bullseye
RUN adduser --disabled-password chess

COPY --from=python /usr/games /usr/games/
COPY --from=uv-install-django /bin/uv /bin/uvx /bin/
COPY --from=uv-install-django /chess/ /chess/
COPY django_chess/ /chess/django_chess/
COPY manage.py start-daphne.sh /chess/

RUN chown -R chess:chess /chess

USER chess

WORKDIR /chess
RUN mkdir /chess/data

# Collect static files
RUN uv run --no-dev python manage.py collectstatic --noinput

# Note that someone -- typically docker-compose -- needs to have run "migrate" first
CMD ["bash", "./start-daphne.sh"]
