"""Bridge to the existing `comercio-exterior-mexico` ETL core.

Per the report: DO NOT rewrite that repo. Encapsulate its jobs as invocable
workers, then migrate its curated DuckDB warehouse into PostgreSQL for the
public API. This module handles the *encapsulation* half (running its CLI);
migrate_duckdb_to_pg.py handles the *migration* half.

Config (in .env):
  COMEX_REPO_PATH   absolute path to the comercio-exterior-mexico checkout
  COMEX_DUCKDB_PATH path to its data/comex.duckdb (defaults to <repo>/data/comex.duckdb)

Run:
  python -m workers.comex_bridge etl            # run all public ETL sources
  python -m workers.comex_bridge etl snice-nico # a single source
  python -m workers.comex_bridge status         # etl_status() from the core
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

COMEX_REPO_PATH = os.getenv(
    "COMEX_REPO_PATH",
    r"C:\Users\jcgam\Downloads\Trabajo\pruebas\comercio-exterior-mexico",
)


def _repo() -> Path:
    repo = Path(COMEX_REPO_PATH)
    if not repo.exists():
        print(f"[comex_bridge] COMEX_REPO_PATH not found: {repo}", file=sys.stderr)
        print("[comex_bridge] Set COMEX_REPO_PATH in .env to the repo checkout.", file=sys.stderr)
    return repo


def _python(repo: Path) -> str:
    """Prefer the repo's own venv so its pinned deps (duckdb, requests) are used."""
    venv_py = repo / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return str(venv_py) if venv_py.exists() else sys.executable


def run_cli(*args: str) -> int:
    """Invoke `python comex.py <args>` inside the existing repo (subprocess)."""
    repo = _repo()
    if not repo.exists():
        return 2
    cmd = [_python(repo), "comex.py", *args]
    print(f"[comex_bridge] $ {' '.join(cmd)}  (cwd={repo})")
    return subprocess.call(cmd, cwd=str(repo))


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: python -m workers.comex_bridge <etl [source] | status | init-db | warehouse-refresh>")
        return 1
    verb, *rest = argv
    if verb == "etl":
        return run_cli("etl", "run", *(rest or []))
    if verb == "status":
        return run_cli("etl", "status")
    if verb in {"init-db", "warehouse-refresh"}:
        return run_cli(verb)
    # Passthrough for any other comex.py subcommand.
    return run_cli(verb, *rest)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
