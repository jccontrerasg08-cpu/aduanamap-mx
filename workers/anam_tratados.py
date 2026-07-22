"""ANAM — tratados / guías / herramientas importer.

Capture stage live (fetch + preserve + manifest + etl_run). La normalización a
`agreement` / `agreement_source_claim` (recordando que SE y ANAM difieren en el
conteo de TLC — no es error, es criterio) queda como TODO por depender del
formato publicado.

Run: ANAM_TRATADOS_URL=<url> python -m workers.anam_tratados
"""
from __future__ import annotations

from workers.common.source_job import capture_only

PARSER_VERSION = "anam_tratados@0"


def run() -> int:
    return capture_only("anam", "ANAM_TRATADOS_URL", parser_version=PARSER_VERSION,
                        content_type="text/html")


if __name__ == "__main__":
    raise SystemExit(run())
