"""DOF — watcher de comercio exterior.

El DOF es la fuente jurídica de publicación formal. Frecuencia sugerida: cada
30 min en horario laboral. Capture stage live (archiva PDF/HTML crudo + manifest);
la detección de decretos/modificaciones y su ligado a agreement_document /
tariff_rate queda como TODO por depender del formato de la nota publicada.

Run: DOF_COMEX_URL=<url> python -m workers.dof_watch
"""
from __future__ import annotations

from workers.common.source_job import capture_only

PARSER_VERSION = "dof_watch@0"


def run() -> int:
    return capture_only("dof", "DOF_COMEX_URL", parser_version=PARSER_VERSION,
                        content_type="text/html")


if __name__ == "__main__":
    raise SystemExit(run())
