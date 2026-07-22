"""AduanaMap MX ETL workers package.

Each module is an invocable job (``python -m workers.<name>``) following the
report pipeline: capture → preserve → parse → normalize → publish. Shared
primitives (robust HTTP, raw-snapshot preservation, manifest + etl_run tracking)
live in ``workers.common``. Jobs run in DRY-RUN when their source/token env var
is unset so the pipeline is exercisable without infra or secrets.
"""
