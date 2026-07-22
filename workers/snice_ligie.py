"""SNICE — LIGIE / NICO importer (Fase 2, stub).

Objetivo: normalizar fracciones de 8 dígitos y su NICO (quinto par → 10 dígitos),
manejando la "compactación" donde varias fracciones convergen en una con distintos NICOs.
Requiere versionado temporal (effective_from/to) y tablas de correlación.

Run: python -m workers.snice_ligie
"""
from __future__ import annotations

PARSER_VERSION = "snice_ligie@0"


def run() -> int:
    print("[snice_ligie] TODO Fase 2 — descargar LIGIE/NICO, snapshot, normalizar "
          "mx_tariff_fraction + mx_nico con versionado. Pipeline en workers/common/manifest.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
