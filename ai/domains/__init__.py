"""Domain registry for the customs assistant — auto-discovered, no central list.

Why this exists: the assistant's knowledge must grow across many independent customs
topics (Harmonized System, LIGIE, NICO, glossary, authorities, regimes, DOF…). If each
topic had to be registered in a shared file, every contribution would collide there.
Instead, this package **discovers modules by globbing `ai/domains/*.py`** — dropping in
a new file is the whole registration step.

## Contract every domain module must satisfy

```python
NAME = "glosario"                 # unique, kebab/snake, used in source_trace
SEED = "glossary.json"            # file in data/seed/ (may be absent → degrade)
PRIORITY = 50                     # optional; lower runs first (default 50)

def match(q: str) -> bool:        # cheap, no I/O: does this domain own the question?
    ...

def answer(q: str, lang: str) -> dict:
    return {
        "answer": "…",            # required: grounded prose, built only from SEED data
        "data": {...},            # optional structured payload
        "sources": [{"source": "SNICE", "label": "sistema armonizado"}],
        "warnings": ["…"],       # optional; use "no confirmable: …" when data is missing
    }
```

Hard rules for domains (enforced by tests in `tests/ai/`):
- **Never state tariff rates, percentages or amounts.** Structure and definitions only.
- **Every fact must come from SEED**, and SEED entries must carry a real `source` URL.
- **Never expose internal paths or env vars** in `sources` — cite domain-facing names.

## Robustness

A broken or malformed domain module must never take down the assistant: discovery
imports each module defensively and simply skips ones that fail or don't satisfy the
contract. `discover()` is cached; call `reset()` in tests after adding modules.
"""
from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

_REQUIRED = ("NAME", "SEED", "match", "answer")
_cache: list[ModuleType] | None = None


def _is_valid(mod: ModuleType) -> bool:
    if not all(hasattr(mod, attr) for attr in _REQUIRED):
        return False
    return callable(mod.match) and callable(mod.answer)


def discover() -> list[ModuleType]:
    """Import every valid domain module, ordered by PRIORITY then NAME."""
    global _cache
    if _cache is not None:
        return _cache
    found: list[ModuleType] = []
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"{__name__}.{info.name}")
        except Exception:
            # A domain that fails to import is skipped, never fatal.
            continue
        if _is_valid(mod):
            found.append(mod)
    found.sort(key=lambda m: (getattr(m, "PRIORITY", 50), getattr(m, "NAME", "")))
    _cache = found
    return _cache


def reset() -> None:
    """Clear the discovery cache (tests that add/remove domain modules)."""
    global _cache
    _cache = None


def names() -> list[str]:
    return [m.NAME for m in discover()]


def find_handler(q: str) -> ModuleType | None:
    """First domain whose match() claims the question, or None."""
    for mod in discover():
        try:
            if mod.match(q):
                return mod
        except Exception:
            continue  # a domain with a broken matcher is skipped, not fatal
    return None


def try_answer(q: str, lang: str = "es") -> dict | None:
    """Route the question to its domain. Returns the domain's dict, or None.

    Normalizes the domain's output so the assistant can consume it uniformly, and
    swallows domain errors (a bad domain degrades to "unanswered", never a 500).
    """
    mod = find_handler(q)
    if mod is None:
        return None
    try:
        res = mod.answer(q, lang) or {}
    except Exception:
        return None
    if not res.get("answer"):
        return None
    return {
        "answer": res["answer"],
        "data": res.get("data") or {},
        "sources": res.get("sources") or [{"source": mod.NAME, "label": "dominio"}],
        "warnings": res.get("warnings") or [],
        "domain": mod.NAME,
    }
