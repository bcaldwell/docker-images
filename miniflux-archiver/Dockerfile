FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . /app

RUN uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "python", "main.py"]