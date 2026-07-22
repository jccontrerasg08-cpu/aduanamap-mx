# workers/Dockerfile — container image for the ETL workers.
# One image runs any job via `docker compose run --rm workers python -m workers.<job>`.
# Installs the `aduanamap-workers` package from pyproject, copies the workers/ tree,
# and defaults to the Banxico FIX job. Real cron scheduling is defined in infra/.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY workers/pyproject.toml ./pyproject.toml
RUN pip install --upgrade pip && pip install .

COPY workers ./workers

# Invoke a specific job, e.g.:
#   docker compose run --rm workers python -m workers.banxico_fix
CMD ["python", "-m", "workers.banxico_fix"]
