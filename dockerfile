FROM python:3.13-slim-bookworm
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

WORKDIR /app

ENTRYPOINT [ "uv", "--version" ]