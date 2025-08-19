FROM python:3.13-slim-bullseye AS python
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt -y update
RUN apt -y install gnuchess

ENV PYTHONUNBUFFERED=t

RUN adduser --disabled-password chess

FROM python AS uv-install-django

COPY uv.lock pyproject.toml /chess/
WORKDIR /chess
RUN ["uv", "sync", "--no-dev"]

FROM python AS app

COPY --from=uv-install-django /chess/ /chess/
COPY django_chess/ /chess/django_chess/
COPY manage.py start-daphne.sh /chess/

RUN chown -R chess:chess /chess

USER chess

WORKDIR /chess
RUN mkdir /chess/data

# Note that someone -- typically docker-compose -- needs to have run "collectstatic" and "migrate" first
CMD ["bash", "./start-daphne.sh"]
