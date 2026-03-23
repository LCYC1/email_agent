FROM python:3.12-slim AS base
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./

# Dev stage: all deps + hot reload
FROM base AS dev
RUN poetry install --no-root
COPY . .
RUN mkdir -p emails logs
EXPOSE ${PORT:-8000}
CMD ["sh", "-c", "poetry run uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000} --reload"]

# Prod stage: production deps only, code baked in
FROM base AS prod
RUN poetry install --only main --no-root
COPY . .
RUN mkdir -p emails logs
EXPOSE ${PORT:-8000}
CMD ["sh", "-c", "poetry run uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
