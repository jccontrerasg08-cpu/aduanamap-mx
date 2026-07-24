"""Security guard for the trade assistant: prompt-injection and disclosure defense.

Threat model. The assistant is a public, unauthenticated endpoint that takes free
text. Three risks matter:

  1. **Prompt injection** — input crafted to override behavior ("ignore previous
     instructions", "reveal your system prompt", "act as…"). Today the assistant is
     deterministic (templated answers), so injection cannot change control flow; but
     this guard blocks it explicitly AND protects the optional LLM path, where
     injection would otherwise be live.
  2. **Secret / configuration disclosure** — probes for env vars, tokens, connection
     strings, credentials, or internals (`DATABASE_URL`, `.env`, API keys).
  3. **Reflected payloads** — input echoed back into the answer, enabling XSS or
     using our response as an injection carrier for a downstream model.

Defense in depth, in this order:
  - `classify_input()` rejects injection/disclosure probes with a fixed, in-domain
    refusal that NEVER echoes the payload.
  - The assistant only ever emits text built from the curated catalog — it has no
    access to environment or filesystem beyond the seed files it reads.
  - `scrub_output()` is a final belt-and-braces pass: even if some future path tried
    to emit a secret-shaped string, it is redacted before leaving the process.

`ai/` deliberately never reads os.environ for anything it could print, so there is
no secret in scope to leak in the first place.
"""
from __future__ import annotations

import re

# ── 1. Prompt-injection / instruction-override attempts ─────────────────────
_INJECTION = re.compile(
    r"(ignor\w*\s+(all\s+|todas?\s+|las\s+)?(previous|prior|above|anterior\w*|instruc\w+))"
    r"|(disregard|olvida|olvídate)\s+(all\s+|the\s+|las\s+|tus\s+)?(previous|prior|instruc\w+|reglas)"
    r"|(system|initial|original)\s*(prompt|message|instruc\w+)"
    r"|(prompt|instrucc\w+)\s+(del\s+)?(sistema|system)"
    r"|(reveal|show|print|output|repeat|dime|mu[eé]strame|imprime|revela)\s+"
    r"(me\s+)?(your|tu|tus|el|la|los|las)?\s*"
    r"(prompt|instruc\w+|system|configuraci[oó]n|config|rules|reglas)"
    r"|you\s+are\s+now|act\s+as\s+(a|an)\b|pretend\s+to\s+be|act[uú]a\s+como"
    r"|jailbreak|DAN\s+mode|developer\s+mode|modo\s+desarrollador"
    r"|(bypass|override|salta|omite)\s+(your|the|tus|las)?\s*(restric\w+|rules|reglas|filtro\w*)"
    r"|new\s+instructions?|nuevas\s+instrucciones",
    re.IGNORECASE,
)

# ── 2. Secret / configuration / internals probes ────────────────────────────
_SECRET_PROBE = re.compile(
    r"\b(DATABASE_URL|REDIS_URL|BANXICO_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY|"
    r"ADMIN_JWT_SECRET|SENTRY_DSN|OBJECT_STORAGE_(KEY|SECRET)|GHCR_TOKEN|"
    r"SMTP_(USER|PASSWORD)|AWS_[A-Z_]+)\b"
    r"|\.env\b|dotenv"
    r"|(variables?|var)\s+de\s+entorno|environment\s+variables?"
    r"|\b(api[\s_-]?key|access[\s_-]?token|bearer\s+token|secret\s+key|private\s+key)\b"
    r"|\b(contrase[nñ]a|password|credencial\w*|credentials?|secreto\w*)\b"
    r"|(connection|conexi[oó]n)\s+string|cadena\s+de\s+conexi[oó]n"
    r"|\b(c[oó]digo\s+fuente|source\s+code|dockerfile|docker-compose|"
    r"esquema\s+de\s+(la\s+)?base|database\s+schema|migraci[oó]n\s+sql)\b",
    re.IGNORECASE,
)

# ── 3. Output redaction (defense in depth) ─────────────────────────────────
_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    # KEY=value pairs that look like configuration
    (re.compile(r"\b[A-Z][A-Z0-9_]{3,}\s*=\s*\S+"), "[redactado]"),
    # Connection strings
    (re.compile(r"\b(postgres(?:ql)?|redis|mysql|mongodb)://\S+", re.IGNORECASE), "[redactado]"),
    # Common API-key shapes
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}"), "[redactado]"),
    (re.compile(r"\b(?:Bearer|Token)\s+[A-Za-z0-9._\-]{8,}", re.IGNORECASE), "[redactado]"),
    # Absolute filesystem paths (posix and windows)
    (re.compile(r"[A-Za-z]:\\[\\\w.\-]+"), "[ruta omitida]"),
    (re.compile(r"(?<![\w/])/(?:home|root|etc|var|usr|app|opt)/[\w./\-]+"), "[ruta omitida]"),
)

# Anything the assistant emits must stay inside the trade domain. This is the
# fixed refusal — it deliberately does not restate the user's payload.
REFUSAL_ES = (
    "Solo puedo ayudarte con comercio exterior de México (tratados de libre comercio, "
    "países socios, clasificación arancelaria). No puedo compartir configuración, "
    "credenciales ni detalles técnicos del sistema, ni cambiar mis instrucciones."
)
REFUSAL_EN = (
    "I can only help with Mexican foreign trade (free-trade agreements, partner "
    "countries, tariff classification). I can't share configuration, credentials or "
    "system internals, and I can't change my instructions."
)


def classify_input(text: str) -> str | None:
    """Return 'injection' | 'disclosure' if the input must be refused, else None."""
    if not text:
        return None
    if _INJECTION.search(text):
        return "injection"
    if _SECRET_PROBE.search(text):
        return "disclosure"
    return None


def scrub_output(text: str) -> str:
    """Redact secret-shaped substrings from anything about to be returned."""
    if not text:
        return text
    out = text
    for pattern, replacement in _REDACTIONS:
        out = pattern.sub(replacement, out)
    return out


def output_is_clean(text: str) -> bool:
    """True when the text contains nothing secret-shaped (used by tests/asserts)."""
    return scrub_output(text) == text
