"""Canonical knowledge base for the trade assistant.

Loads the repo's curated seed data — Mexico's FTAs (data/seed/agreements.json) and
the country catalog (apps/web/public/geo/countries-50m.geojson) — into memory and
exposes deterministic lookups. This is what keeps the assistant GROUNDED: it can
only reference facts that exist here, so it never invents an agreement, a member,
or a date (ADR 0002).

Works with no database and no LLM — the data is read straight from the repo, so
the assistant degrades gracefully and is fully testable offline. Paths can be
overridden with AGREEMENTS_SEED_PATH / COUNTRIES_GEOJSON_PATH.
"""
from __future__ import annotations

import json
import os
import unicodedata
from functools import lru_cache
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
_REPO = _AI_DIR.parent


def _first_existing(env: str, *candidates: Path) -> Path | None:
    override = os.getenv(env)
    if override and Path(override).exists():
        return Path(override)
    for c in candidates:
        if c.exists():
            return c
    return None


def _agreements_path() -> Path | None:
    return _first_existing(
        "AGREEMENTS_SEED_PATH",
        _REPO / "data" / "seed" / "agreements.json",
        Path.cwd() / "data" / "seed" / "agreements.json",
        _AI_DIR / "data" / "agreements.json",  # Docker: copied next to the package
    )


def _countries_path() -> Path | None:
    return _first_existing(
        "COUNTRIES_GEOJSON_PATH",
        _REPO / "apps" / "web" / "public" / "geo" / "countries-50m.geojson",
        Path.cwd() / "apps" / "web" / "public" / "geo" / "countries-50m.geojson",
        _AI_DIR / "data" / "countries-50m.geojson",
    )


def _norm(text: str) -> str:
    """Lowercase + strip accents, for tolerant name matching (Japón == japon)."""
    n = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in n if not unicodedata.combining(c)).strip()


@lru_cache(maxsize=1)
def _agreements_doc() -> dict:
    p = _agreements_path()
    if p is None:
        return {"agreements": [], "source_claims": [], "_meta": {}}
    return json.loads(p.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _countries() -> list[dict]:
    p = _countries_path()
    if p is None:
        return []
    fc = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for f in fc.get("features", []):
        pr = f.get("properties", {})
        if pr.get("iso3"):
            out.append({
                "iso3": pr["iso3"], "iso2": pr.get("iso2"),
                "name_es": pr.get("name_es"), "name_en": pr.get("name_en"),
                "region": pr.get("region"),
            })
    return out


def data_available() -> bool:
    return bool(_agreements_doc().get("agreements"))


# ── Country resolution ──────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def _country_index() -> dict[str, dict]:
    """Map of normalized name / iso2 / iso3 → country row, for fuzzy resolution."""
    idx: dict[str, dict] = {}
    # A few common Spanish aliases Natural Earth/world-countries don't carry.
    aliases = {
        "estados unidos": "USA", "eeuu": "USA", "usa": "USA", "corea del sur": "KOR",
        "reino unido": "GBR", "inglaterra": "GBR", "paises bajos": "NLD", "holanda": "NLD",
    }
    for c in _countries():
        for key in (c["iso3"], c.get("iso2"), c.get("name_es"), c.get("name_en")):
            if key:
                idx[_norm(key)] = c
    for alias, iso3 in aliases.items():
        hit = next((c for c in _countries() if c["iso3"] == iso3), None)
        if hit:
            idx[alias] = hit
    return idx


def resolve_country(text: str, exclude_home: bool = True) -> dict | None:
    """Resolve a free-text country mention to a country row, or None.

    Mexico is the implicit home country of the whole product, so a mentioned
    country is always a *partner* — MEX is excluded by default. Without this,
    "¿México tiene TLC con Japón?" would resolve to Mexico, not Japan.
    """
    if not text:
        return None
    idx = _country_index()
    t = _norm(text)
    if t in idx and not (exclude_home and idx[t]["iso3"] == "MEX"):
        return idx[t]
    # token scan: find the longest country name appearing in the text
    best = None
    for name, c in idx.items():
        if len(name) < 4 or (exclude_home and c["iso3"] == "MEX"):
            continue
        if name in t and (best is None or len(name) > len(best[0])):
            best = (name, c)
    return best[1] if best else None


# ── Agreement lookups ───────────────────────────────────────────────────────
def agreements(active_only: bool = True) -> list[dict]:
    items = _agreements_doc().get("agreements", [])
    return [a for a in items if a.get("status") == "active"] if active_only else list(items)


def get_agreement(slug: str) -> dict | None:
    return next((a for a in _agreements_doc().get("agreements", []) if a["slug"] == slug), None)


def find_agreement_by_name(text: str) -> dict | None:
    t = _norm(text)
    for a in _agreements_doc().get("agreements", []):
        if _norm(a["name_es"]) in t or _norm(a["name_en"]) in t or a["slug"] in t:
            return a
    # common acronyms
    for acro, slug in {"t-mec": "t-mec", "tmec": "t-mec", "usmca": "t-mec", "cptpp": "cptpp-tipat",
                       "tipat": "cptpp-tipat", "tlcuem": "tlcuem", "efta": "tlc-aelc-efta",
                       "aelc": "tlc-aelc-efta"}.items():
        if acro in t:
            return get_agreement(slug)
    return None


def agreements_for_country(iso3: str, active_only: bool = True) -> list[dict]:
    return [a for a in agreements(active_only) if iso3 in a.get("members", [])]


def partner_country_count(active_only: bool = True) -> int:
    partners: set[str] = set()
    for a in agreements(active_only):
        partners.update(a.get("members", []))
    return len(partners)


def source_claims() -> list[dict]:
    return _agreements_doc().get("source_claims", [])


def consulted_at() -> str | None:
    return _agreements_doc().get("_meta", {}).get("consulted_at")
