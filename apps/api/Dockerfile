# apps/api/Dockerfile — container image for the FastAPI public read API.
# Build context is the repo root (see docker-compose.yml) so the shared layout is
# available. Installs the `aduanamap-api` package from pyproject, copies the app,
# and serves uvicorn on :8000. Layer order (deps before source) maximizes caching.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY apps/api/pyproject.toml ./pyproject.toml
RUN pip install --upgrade pip && pip install .

COPY apps/api/app ./app

# The narrow AI layer + the curated seed data it reads. Kept as sibling paths so
# `ai/` cannot import the API's rate logic (ADR 0002) and the assistant works with
# no database. The router locates `ai/` by walking parent dirs, so /app works.
COPY ai ./ai
COPY data/seed ./data/seed

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
