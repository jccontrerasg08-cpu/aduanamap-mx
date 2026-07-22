"""SNICE — LIGIE / NICO importer.

Capture stage is live (fetch + preserve + manifest + etl_run). The normalize
stage — fracciones de 8 dígitos y su NICO (quinto par → 10 dígitos), con
"compactación" donde varias fracciones convergen en una con distintos NICOs, y
versionado temporal (effective_from/to) — queda como TODO por depender del
formato exacto de la fuente (XLSX/HTML), que debe verificarse contra un snapshot
real antes de escribir el parser.

Run: SNICE_LIGIE_URL=<url> python -m workers.snice_ligie
"""
from __future__ import annotations

from workers.common.source_job import capture_only

PARSER_VERSION = "snice_ligie@0"


def run() -> int:
    return capture_only(
        "snice", "SNICE_LIGIE_URL", parser_version=PARSER_VERSION,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    raise SystemExit(run())
