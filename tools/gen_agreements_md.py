"""Generate docs/tlc-mexico.md from data/seed/agreements.json.

The JSON stays the single source of truth (it is what the API, the assistant and
the map read); this script renders the human-readable Markdown view so the two can
never drift. Re-run after editing the seed:

    python tools/gen_agreements_md.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed" / "agreements.json"
OUT = ROOT / "docs" / "tlc-mexico.md"

FTA_TYPES = {"FTA", "regional", "plurilateral"}
PARTIAL_TYPES = {"ACE", "AAP"}


def members(a: dict) -> str:
    m = a.get("members", [])
    return f"{len(m)} — " + ", ".join(m) if len(m) > 3 else ", ".join(m)


def table(rows: list[dict], *, show_notes: bool = True) -> list[str]:
    out = ["| Instrumento | Miembros (socios de México) | Firma | Vigencia |",
           "|---|---|---:|---:|"]
    for a in rows:
        out.append(f"| **{a['name_es']}** | {members(a)} | {a.get('signed_date') or '—'} "
                   f"| {a.get('effective_date') or '—'} |")
    if show_notes:
        notes = [a for a in rows if a.get("notes")]
        if notes:
            out.append("")
            for a in notes:
                out.append(f"- **{a['name_es']}**: {a['notes']}")
    return out


def main() -> int:
    doc = json.loads(SEED.read_text(encoding="utf-8"))
    ags = doc["agreements"]
    meta = doc.get("_meta", {})
    cov = meta.get("coverage", {})

    active_fta = [a for a in ags if a["status"] == "active" and a["type"] in FTA_TYPES]
    partial = [a for a in ags if a["status"] == "active" and a["type"] in PARTIAL_TYPES]
    superseded = [a for a in ags if a["status"] == "superseded"]

    partners = sorted({m for a in active_fta for m in a.get("members", [])})

    L: list[str] = [
        "# Tratados y acuerdos comerciales de México",
        "",
        "> **Documento generado.** No lo edites a mano: modifica "
        "[`data/seed/agreements.json`](../data/seed/agreements.json) y ejecuta "
        "`python tools/gen_agreements_md.py`.",
        "",
        f"**Última consulta de fuentes:** {meta.get('consulted_at', '—')}",
        "",
        "## Resumen",
        "",
        f"- **{len(active_fta)}** instrumentos de libre comercio vigentes",
        f"- **{len(partners)}** países socios distintos bajo esos instrumentos",
        f"- **{len(partial)}** acuerdos de alcance parcial/sectorial de ALADI (**no son TLC**)",
        f"- **{len(superseded)}** instrumentos superados, conservados por trazabilidad histórica",
        "",
        "> ⚠️ Un **ACE/AAP no es un TLC**: otorga preferencias sobre un universo limitado "
        "de productos, no libre comercio pleno.",
        "",
        "## Tratados de libre comercio vigentes",
        "",
    ]
    L += table(active_fta)

    L += ["", "## Acuerdos de alcance parcial / sectorial (ALADI) — NO son TLC", ""]
    L += table(partial)

    L += ["", "## Instrumentos superados (historial)", ""]
    L += table(superseded)

    L += ["", "## Conteo según fuente", "",
          "El total **difiere entre fuentes oficiales** por criterio de agrupación. No es un "
          "error de datos: se registra cada afirmación por separado.", "",
          "| Fuente | Afirmación | Valor | Consultado | Nota |", "|---|---|---:|---:|---|"]
    for c in doc.get("source_claims", []):
        L.append(f"| {c['source_name']} | {c['claim_type']} | **{c['claim_value']}** "
                 f"| {c['consulted_at']} | {c.get('notes', '')} |")

    L += ["", "## Cobertura de este catálogo", "",
          f"- **Incluido:** {cov.get('included', '—')}",
          f"- **No enumerado:** {cov.get('not_enumerated', '—')}", "",
          "## Países socios (instrumentos de libre comercio)", "",
          "`" + " ".join(partners) + "`", "",
          "## Fuentes", ""]
    for s in meta.get("sources", []):
        L.append(f"- {s}")
    L += ["", "---", "",
          "Documento informativo. No constituye asesoría legal, fiscal ni aduanera. "
          "Verifica siempre la fuente primaria antes de operar."]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"escrito {OUT.relative_to(ROOT)}: {len(active_fta)} TLC, {len(partial)} alcance parcial, "
          f"{len(superseded)} superados, {len(partners)} países socios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
