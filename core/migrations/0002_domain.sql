-- 0002_domain.sql — remaining domain tables from the deep-research report.
-- Depends on 0001_init.sql. Idempotent-friendly (IF NOT EXISTS) so re-running is safe.

BEGIN;

-- ── Documentos de acuerdos (DOF, PDF, texto integrado, anexos) ──────────────
CREATE TABLE IF NOT EXISTS agreement_document (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agreement_id       UUID NOT NULL REFERENCES agreement(id) ON DELETE CASCADE,
  document_type      TEXT NOT NULL,            -- texto | anexo | decreto_dof | protocolo
  title              TEXT NOT NULL,
  source_document_id UUID REFERENCES source_document(id),
  effective_date     DATE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agreement_document_agreement ON agreement_document (agreement_id);

-- ── Tasas arancelarias (solo desde fuente estructurada; nunca inferidas) ─────
CREATE TABLE IF NOT EXISTS tariff_rate (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  target_type        TEXT NOT NULL,            -- fraccion8 | nico10 | hs6
  target_code        TEXT NOT NULL,
  rate_type          TEXT NOT NULL,            -- igi | ige | preferencial | cupo
  agreement_id       UUID REFERENCES agreement(id),
  import_rate        NUMERIC(9,4),
  export_rate        NUMERIC(9,4),
  currency           CHAR(3),
  unit               TEXT,
  effective_from     DATE NOT NULL,
  effective_to       DATE,
  source_document_id UUID REFERENCES source_document(id),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tariff_rate_code ON tariff_rate (target_code, effective_from DESC);

-- ── Autoridades y sus requisitos (regulaciones/restricciones no arancelarias) ─
CREATE TABLE IF NOT EXISTS authority (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug         TEXT NOT NULL,
  name_es      TEXT NOT NULL,
  name_en      TEXT NOT NULL,
  summary_es   TEXT,
  summary_en   TEXT,
  official_url TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_authority_slug UNIQUE (slug)
);

CREATE TABLE IF NOT EXISTS authority_requirement (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  authority_id        UUID NOT NULL REFERENCES authority(id) ON DELETE CASCADE,
  target_type         TEXT NOT NULL,           -- fraccion8 | nico10 | hs6
  target_code         TEXT NOT NULL,
  requirement_type    TEXT NOT NULL,           -- permiso | nom | aviso | cupo
  requirement_summary TEXT,
  legal_basis_doc_id  UUID REFERENCES source_document(id),
  effective_from      DATE,
  effective_to        DATE
);
CREATE INDEX IF NOT EXISTS idx_authority_requirement_code ON authority_requirement (target_code);

-- ── Reglas de origen por tratado + producto (HS6). Nunca calculadas por IA. ──
CREATE TABLE IF NOT EXISTS rule_of_origin (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agreement_id       UUID NOT NULL REFERENCES agreement(id) ON DELETE CASCADE,
  hs6                CHAR(6) NOT NULL,
  rule_text_es       TEXT,
  proof_type         TEXT,                     -- certificado | declaracion | autocertificacion
  source_document_id UUID REFERENCES source_document(id),
  effective_from     DATE,
  effective_to       DATE
);
CREATE INDEX IF NOT EXISTS idx_rule_of_origin_agreement_hs6 ON rule_of_origin (agreement_id, hs6);

-- ── Contenido editorial bilingüe ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wiki_page (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug             TEXT NOT NULL,
  kind             TEXT NOT NULL,              -- country | agreement | authority | guide | glossary | faq
  lang             CHAR(2) NOT NULL,
  title            TEXT NOT NULL,
  summary          TEXT,
  body_md          TEXT,
  status           TEXT NOT NULL DEFAULT 'draft',   -- draft | published
  canonical_path   TEXT,
  last_verified_at TIMESTAMPTZ,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_wiki_slug_lang UNIQUE (slug, lang)
);

-- ── Búsqueda full-text (tsvector + GIN) ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS search_index (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind      TEXT NOT NULL,                     -- hs | fraccion | nico | country | agreement | wiki
  entity_id TEXT NOT NULL,
  lang      CHAR(2) NOT NULL,
  title     TEXT NOT NULL,
  body      TEXT,
  body_tsv  TSVECTOR,
  boost     REAL NOT NULL DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS idx_search_index_tsv ON search_index USING GIN (body_tsv);

-- ── Casos de calculadora (anónimos por defecto; PII minimizada) ─────────────
CREATE TABLE IF NOT EXISTS calculator_case (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  anonymous_token TEXT,
  country_origin  CHAR(3),
  country_export  CHAR(3),
  mx_code         TEXT,
  invoice_value   NUMERIC(18,2),
  currency        CHAR(3),
  incoterm        TEXT,
  freight         NUMERIC(18,2),
  insurance       NUMERIC(18,2),
  result_json     JSONB,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_calculator_case_created ON calculator_case (created_at DESC);

COMMIT;
