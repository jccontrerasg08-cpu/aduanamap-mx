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

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
