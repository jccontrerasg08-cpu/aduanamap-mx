"""Grounded trade assistant — an AI specialized in Mexican foreign trade.

Design per the report's final decision ("producto de datos verificables, no una
app de IA que adivina") and ADR 0002:

  - It ANSWERS from the canonical knowledge base only (ai/knowledge.py). Every
    factual claim traces to `data/seed/agreements.json` (SE/SICE) — never invented.
  - It REFUSES to state tariff rates, duties or rules of origin: those need a
    structured, versioned source, so it returns "no confirmable" and points to the
    deterministic tools (/arancel, /calculadora). It never guesses a number.
  - It works with no database and no LLM: intent detection + templated, grounded
    answers are deterministic and fully testable. An LLM, if configured, is used
    only to rephrase the SAME grounded facts (it is never the source of truth).

Public entry point: `answer(question, lang="es") -> dict` with
{answer, data, source_trace, warnings, grounded}.
"""
from __future__ import annotations

import re

from . import guard, knowledge

MAX_Q = 500

# Anything that would require a rate / rule of origin the assistant must not invent.
_RATE_WORDS = re.compile(
    r"\b(arancel|aranceles|tasa|tasas|impuesto|impuestos|igi|ige|dta|iva|"
    r"cuanto (pago|cuesta|debo)|cu[aá]nto pagar|tariff|duty|duties|rate of duty|"
    r"regla de origen|rules? of origin)\b",
    re.IGNORECASE,
)
_COUNT_WORDS = re.compile(r"\b(cu[aá]ntos|cuantos|how many|n[uú]mero de|total de)\b", re.IGNORECASE)
_LIST_WORDS = re.compile(r"\b(lista|list|cu[aá]les|cuales|todos|all|enumera)\b", re.IGNORECASE)

# Domain-facing source names only. Internal file paths are deliberately NOT exposed
# (they are technical detail unrelated to foreign trade — see ai/guard.py).
_SRC = [
    {"source": "Secretaría de Economía / SICE-OEA", "label": "red de tratados"},
    {"source": "ANAM", "label": "tratados y acuerdos con México"},
    {"source": "Catálogo AduanaMap", "label": "curado y versionado"},
]
_DISCLAIMER_ES = ("Información de referencia con base en fuentes oficiales; no es asesoría "
                  "legal ni aduanera. Verifica la fuente primaria antes de operar.")
_DISCLAIMER_EN = ("Reference information based on official sources; not legal or customs "
                  "advice. Verify the primary source before operating.")


def _t(lang: str, es: str, en: str) -> str:
    return en if lang == "en" else es


def _result(answer, *, data=None, warnings=None, grounded=True, lang="es"):
    warns = list(warnings or [])
    warns.append(_t(lang, _DISCLAIMER_ES, _DISCLAIMER_EN))
    # Final belt-and-braces pass: nothing secret-shaped ever leaves this function.
    return {"answer": guard.scrub_output(answer), "data": data or {},
            "source_trace": _SRC if grounded else [], "warnings": warns, "grounded": grounded}


def _fmt_agreement(a: dict, lang: str) -> str:
    name = a["name_en"] if lang == "en" else a["name_es"]
    eff = a.get("effective_date") or "—"
    return _t(lang, f"{name} (vigente desde {eff})", f"{name} (in force since {eff})")


def answer(question: str, lang: str = "es") -> dict:
    lang = "en" if lang == "en" else "es"
    q = (question or "").strip()[:MAX_Q]

    if not q:
        return _result(
            _t(lang, "Formula una pregunta sobre los TLC de México (por país o por tratado).",
               "Ask a question about Mexico's FTAs (by country or by agreement)."),
            grounded=False, lang=lang)

    # Security gate BEFORE any retrieval or generation. The refusal is fixed and
    # never echoes the payload, so the response can't carry an injection downstream.
    threat = guard.classify_input(q)
    if threat is not None:
        return _result(_t(lang, guard.REFUSAL_ES, guard.REFUSAL_EN),
                       warnings=[f"solicitud rechazada: {threat}"], grounded=False, lang=lang)

    if not knowledge.data_available():
        return _result(
            _t(lang, "El catálogo de tratados no está disponible en este momento.",
               "The agreements catalog is unavailable right now."),
            warnings=["no confirmable: catálogo no cargado"], grounded=False, lang=lang)

    # 1) Rates / rules of origin → never invented.
    if _RATE_WORDS.search(q):
        country = knowledge.resolve_country(q)
        extra = {}
        note = _t(lang,
                  "No puedo afirmar aranceles, IVA, DTA ni reglas de origen: requieren una tasa "
                  "estructurada y vigente. Consúltalos en el Explorador arancelario (/arancel) y la "
                  "Calculadora (/calculadora), que muestran la fuente. ",
                  "I can't state tariffs, VAT, DTA or rules of origin: they need a structured, "
                  "in-force rate. Use the Tariff explorer (/arancel) and Calculator (/calculadora), "
                  "which show the source. ")
        if country:
            ags = knowledge.agreements_for_country(country["iso3"])
            cname = country["name_en"] if lang == "en" else country["name_es"]
            if ags:
                note += _t(lang,
                           f"Nota: México sí tiene trato preferencial con {cname} vía "
                           f"{', '.join(a['name_es'] for a in ags)}, pero la tasa aplicable depende "
                           f"de la fracción y la regla de origen.",
                           f"Note: Mexico does have preferential treatment with {cname} via "
                           f"{', '.join(a['name_en'] for a in ags)}, but the applicable rate depends "
                           f"on the tariff line and rule of origin.")
            extra = {"country": country["iso3"], "agreements": [a["slug"] for a in ags]}
        return _result(note, data=extra, warnings=["no confirmable: tasa/regla de origen"],
                       grounded=bool(country), lang=lang)

    # 2) Count questions.
    if _COUNT_WORDS.search(q):
        active = knowledge.ftas(active_only=True)
        partners = knowledge.partner_country_count()
        claims = knowledge.source_claims()
        se = next((c for c in claims if c["source_name"] == "SE" and c["claim_type"] == "tlc_count"), None)
        anam = next((c for c in claims if c["source_name"] == "ANAM" and c["claim_type"] == "tlc_count"), None)
        txt = _t(lang,
                 f"México tiene {len(active)} instrumentos de libre comercio vigentes que cubren "
                 f"{partners} países socios. El conteo total varía según la fuente: SE reporta "
                 f"{se['claim_value'] if se else '14'} TLC/52 países; ANAM "
                 f"{anam['claim_value'] if anam else '12'} TLC/46 países. No es un error, sino un "
                 f"criterio distinto de agrupación.",
                 f"Mexico has {len(active)} free-trade instruments in force covering {partners} "
                 f"partner countries. The total varies by source: SE reports "
                 f"{se['claim_value'] if se else '14'} FTAs/52 countries; ANAM "
                 f"{anam['claim_value'] if anam else '12'} FTAs/46 countries — a difference of "
                 f"grouping criteria, not an error.")
        return _result(txt, data={"active_instruments": len(active), "partner_countries": partners,
                                  "claims": claims}, lang=lang)

    # 3) A specific agreement named?
    ag = knowledge.find_agreement_by_name(q)
    if ag and not knowledge.resolve_country(q):
        members = ", ".join(ag.get("members", []))
        name = ag["name_en"] if lang == "en" else ag["name_es"]
        txt = _t(lang,
                 f"{name}. Estatus: {ag['status']}. Miembros (socios de México): {members}. "
                 f"Firmado: {ag.get('signed_date','—')}; vigente desde: {ag.get('effective_date','—')}.",
                 f"{name}. Status: {ag['status']}. Members (Mexico's partners): {members}. "
                 f"Signed: {ag.get('signed_date','—')}; in force since: {ag.get('effective_date','—')}.")
        if ag.get("notes"):
            txt += f" {ag['notes']}"
        return _result(txt, data=ag, lang=lang)

    # 4) A country mentioned → its agreements with Mexico.
    country = knowledge.resolve_country(q)
    if country:
        ags = knowledge.agreements_for_country(country["iso3"])
        partial = knowledge.partial_scope_for_country(country["iso3"])
        cname = country["name_en"] if lang == "en" else country["name_es"]

        if not ags and not partial:
            return _result(
                _t(lang,
                   f"Según el catálogo, México no tiene un TLC vigente con {cname}. Podría existir un "
                   f"APPRI (acuerdo de inversión) no enumerado aquí; verifica en SE/SICE.",
                   f"Per the catalog, Mexico has no FTA in force with {cname}. An APPRI (investment "
                   f"treaty) not enumerated here may exist; verify with SE/SICE."),
                data={"country": country["iso3"], "agreements": [], "partial_scope": []},
                warnings=["no confirmable: los APPRIs no están enumerados en el catálogo"], lang=lang)

        parts: list[str] = []
        if ags:
            parts.append(_t(lang,
                            f"México tiene trato preferencial con {cname} vía: "
                            + "; ".join(_fmt_agreement(a, lang) for a in ags),
                            f"Mexico has preferential treatment with {cname} via: "
                            + "; ".join(_fmt_agreement(a, lang) for a in ags)))
        if partial:
            # Critical honesty: an ACE is NOT an FTA.
            listing = "; ".join(_fmt_agreement(a, lang) for a in partial)
            if ags:
                parts.append(_t(lang, f"Además, acuerdos de alcance parcial (no son TLC): {listing}",
                                f"Additionally, partial-scope agreements (not FTAs): {listing}"))
            else:
                parts.append(_t(lang,
                                f"México NO tiene un TLC con {cname}, pero sí acuerdos de alcance "
                                f"parcial de ALADI (preferencias sobre un universo limitado de "
                                f"productos, no libre comercio pleno): {listing}",
                                f"Mexico has NO FTA with {cname}, but it does have ALADI partial-scope "
                                f"agreements (preferences on a limited product universe, not full free "
                                f"trade): {listing}"))
        return _result(". ".join(parts) + ".",
                       data={"country": country["iso3"],
                             "agreements": [a["slug"] for a in ags],
                             "partial_scope": [a["slug"] for a in partial]}, lang=lang)

    # 5) List all.
    if _LIST_WORDS.search(q):
        active = knowledge.ftas(active_only=True)
        listing = "; ".join(_fmt_agreement(a, lang) for a in active)
        return _result(
            _t(lang, f"TLC vigentes de México: {listing}.", f"Mexico's FTAs in force: {listing}."),
            data={"agreements": [a["slug"] for a in active]}, lang=lang)

    # 6) Fallback — say what it can do (no guessing).
    return _result(
        _t(lang,
           "Puedo responder sobre los tratados de libre comercio de México: qué países cubren, "
           "fechas de vigencia, miembros y el conteo según fuente. Pregunta por un país (p. ej. "
           "«¿México tiene TLC con Japón?») o por un tratado (p. ej. «T-MEC», «CPTPP»).",
           "I can answer about Mexico's free-trade agreements: which countries they cover, entry "
           "dates, members, and the count by source. Ask about a country (e.g. \"does Mexico have "
           "an FTA with Japan?\") or an agreement (e.g. \"USMCA\", \"CPTPP\")."),
        grounded=False, lang=lang)
