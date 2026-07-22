"""VUCEM — clasificador arancelario / manuales importer.

Capture stage live (fetch + preserve + manifest + etl_run). Alimenta la búsqueda
arancelaria (search_index) una vez escrito el parser del clasificador TIGIE;
esa normalización queda como TODO por depender del formato publicado.

Run: VUCEM_CLASIFICADOR_URL=<url> python -m workers.vucem_clasificador
"""
from __future__ import annotations

from workers.common.source_job import capture_only

PARSER_VERSION = "vucem_clasificador@0"


def run() -> int:
    return capture_only("vucem", "VUCEM_CLASIFICADOR_URL", parser_version=PARSER_VERSION,
                        content_type="text/html")


if __name__ == "__main__":
    raise SystemExit(run())
