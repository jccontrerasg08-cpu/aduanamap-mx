"""Full-text search over the indexed corpus (Postgres tsvector + GIN).

Deterministic ranking (ts_rank). No LLM. Used by /api/tariff/search and, for the
classification *suggestion* path, by /api/classify/suggest — which only proposes
candidates from indexed official descriptions and never asserts a rate.
"""
from __future__ import annotations

from .. import db

# 'spanish' config matches the es descriptions we index; websearch_to_tsquery
# tolerates free-form user input safely (no query-syntax injection).
_SEARCH_Q = """
SELECT kind, entity_id, title, lang,
       ts_rank(body_tsv, websearch_to_tsquery('spanish', %s)) AS score
FROM search_index
WHERE (%s = '' OR lang = %s)
  AND body_tsv @@ websearch_to_tsquery('spanish', %s)
ORDER BY score DESC, boost DESC
LIMIT %s
"""


def search(query: str, *, lang: str = "es", kinds: tuple[str, ...] | None = None,
           limit: int = 10) -> tuple[list[dict], bool]:
    """Return (rows, index_available). Empty rows + False means no index yet."""
    query = (query or "").strip()
    if not query:
        return [], True
    with db.connection() as conn:
        if conn is None:
            return [], False
        try:
            with conn.cursor() as cur:
                cur.execute(_SEARCH_Q, (query, lang, lang, query, limit))
                rows = []
                for kind, entity_id, title, _lang, score in cur.fetchall():
                    if kinds and kind not in kinds:
                        continue
                    rows.append({"kind": kind, "entity_id": entity_id,
                                 "title": title, "score": round(float(score), 4)})
                return rows, True
        except Exception:
            # Table missing / not migrated yet.
            return [], False
