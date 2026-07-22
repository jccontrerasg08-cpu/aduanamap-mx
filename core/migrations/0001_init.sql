-- 0001_init.sql — AduanaMap MX base schema
-- Principio: lo universal es HS; lo nacional es TIGIE/NICO. Todo versionado y trazable.
-- Requiere PostgreSQL 14+ y la extensión PostGIS.

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "postgis";    -- tipos geográficos + GiST

-- ── Trazabilidad de fuentes ─────────────────────────────────────────────────
-- Preservar el archivo crudo importa tanto como la tabla final: un cambio de
-- HTML/XLSX/PDF puede romper el parser sin cambiar el contenido legal.
CREATE TABLE source_manifest (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name    TEXT NOT NULL,                 -- banxico | snice | vucem | anam | dof | wco | wits | sre
  source_url     TEXT NOT NULL,
  sha256         TEXT NOT NULL,
  fetched_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  effective_date DATE,
  parser_version TEXT NOT NULL,
  status         TEXT NOT NULL,                 -- ok | stale | error
  records_loaded INTEGER NOT NULL DEFAULT 0,
  notes          TEXT
);
CREATE INDEX idx_source_manifest_name_fetched ON source_manifest (source_name, fetched_at DESC);

CREATE TABLE source_document (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  manifest_id  UUID NOT NULL REFERENCES source_manifest(id) ON DELETE CASCADE,
  title        TEXT,
  mime_type    TEXT,
  storage_key  TEXT,                            -- llave en object storage del snapshot crudo
  raw_url      TEXT,
  published_at TIMESTAMPTZ,
  hash_sha256  TEXT NOT NULL
);
CREATE INDEX idx_source_document_manifest ON source_document (manifest_id);

-- ── Catálogo geográfico y de acuerdos ───────────────────────────────────────
CREATE TABLE country (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  iso2       CHAR(2) NOT NULL,
  iso3       CHAR(3) NOT NULL,
  name_es    TEXT NOT NULL,
  name_en    TEXT NOT NULL,
  region     TEXT,
  subregion  TEXT,
  active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_country_iso2 UNIQUE (iso2),
  CONSTRAINT uq_country_iso3 UNIQUE (iso3)
);

CREATE TABLE country_geometry (
  country_id  UUID PRIMARY KEY REFERENCES country(id) ON DELETE CASCADE,
  geom        GEOMETRY(MultiPolygon, 4326) NOT NULL,
  bbox        GEOMETRY(Polygon, 4326),
  source_name TEXT NOT NULL,
  source_hash TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_country_geometry_geom ON country_geometry USING GIST (geom);

CREATE TABLE agreement (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug           TEXT NOT NULL,
  name_es        TEXT NOT NULL,
  name_en        TEXT NOT NULL,
  type           TEXT,                          -- FTA | APPRI | ALADI | ...
  status         TEXT,                          -- active | signed | superseded
  signed_date    DATE,
  effective_date DATE,
  source_policy  TEXT,                          -- criterio/fuente del conteo (SE vs ANAM difieren)
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_agreement_slug UNIQUE (slug)
);

CREATE TABLE agreement_member (
  agreement_id UUID NOT NULL REFERENCES agreement(id) ON DELETE CASCADE,
  country_id   UUID NOT NULL REFERENCES country(id)   ON DELETE CASCADE,
  role         TEXT,
  valid_from   DATE,
  valid_to     DATE,
  PRIMARY KEY (agreement_id, country_id)
);

-- Conteos "según fuente" — SE reporta 14 TLC/52 países; ANAM 12 TLC/46 países.
-- No es un error de datos: es diferencia de criterio. Se guarda por afirmación.
CREATE TABLE agreement_source_claim (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name   TEXT NOT NULL,                  -- SE | ANAM | SRE | SNICE
  claim_type    TEXT NOT NULL,                  -- tlc_count | country_count | ...
  claim_value   TEXT NOT NULL,
  consulted_at  DATE NOT NULL,
  source_document_id UUID REFERENCES source_document(id),
  notes         TEXT
);

-- ── Nomenclatura: HS (mundial) → Fracción 8 → NICO 10 (México) ───────────────
CREATE TABLE hs_code (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  hs_version     TEXT NOT NULL,                 -- 2012 | 2017 | 2022 (no asumir correspondencia eterna)
  hs2            CHAR(2) NOT NULL,
  hs4            CHAR(4),
  hs6            CHAR(6),
  description_es TEXT,
  description_en TEXT,
  wco_ref        TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_hs_code_hs6         ON hs_code (hs6);
CREATE INDEX idx_hs_code_version_hs6 ON hs_code (hs_version, hs6);

CREATE TABLE mx_tariff_fraction (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ligie_version      TEXT NOT NULL,
  fraccion8          CHAR(8) NOT NULL,
  hs6                CHAR(6) NOT NULL,
  description_es     TEXT NOT NULL,
  unit               TEXT,
  effective_from     DATE NOT NULL,
  effective_to       DATE,
  source_document_id UUID REFERENCES source_document(id),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_fraction_version UNIQUE (ligie_version, fraccion8, effective_from)
);
CREATE INDEX idx_mx_tariff_fraction_fraccion8 ON mx_tariff_fraction (fraccion8);
CREATE INDEX idx_mx_tariff_fraction_hs6       ON mx_tariff_fraction (hs6);

CREATE TABLE mx_nico (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nico10             CHAR(10) NOT NULL,
  fraccion8          CHAR(8) NOT NULL,
  nico2              CHAR(2) NOT NULL,          -- quinto par de dígitos
  description_es     TEXT NOT NULL,
  effective_from     DATE NOT NULL,
  effective_to       DATE,
  source_document_id UUID REFERENCES source_document(id),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_nico_version UNIQUE (nico10, effective_from)
);
CREATE INDEX idx_mx_nico_nico10    ON mx_nico (nico10);
CREATE INDEX idx_mx_nico_fraccion8 ON mx_nico (fraccion8);

-- ── Datos económicos (Banxico) ──────────────────────────────────────────────
CREATE TABLE banxico_series (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  series_id      TEXT NOT NULL,                 -- p.ej. SF43718 (FIX)
  title_es       TEXT,
  title_en       TEXT,
  frequency      TEXT,
  unit           TEXT,
  catalog_source TEXT,
  CONSTRAINT uq_banxico_series UNIQUE (series_id)
);

CREATE TABLE exchange_rate (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  series_id          TEXT NOT NULL,
  date               DATE NOT NULL,
  value              NUMERIC(18,6) NOT NULL,
  currency_from      CHAR(3) DEFAULT 'USD',
  currency_to        CHAR(3) DEFAULT 'MXN',
  published_at       TIMESTAMPTZ,
  source_manifest_id UUID REFERENCES source_manifest(id),
  CONSTRAINT uq_exchange_rate UNIQUE (series_id, date)
);

-- ── Observabilidad ETL ──────────────────────────────────────────────────────
CREATE TABLE etl_run (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name TEXT NOT NULL,
  started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status      TEXT NOT NULL DEFAULT 'running',  -- running | ok | error
  rows_read   INTEGER NOT NULL DEFAULT 0,
  rows_loaded INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_etl_run_source_started ON etl_run (source_name, started_at DESC);

CREATE TABLE etl_error_log (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  etl_run_id UUID NOT NULL REFERENCES etl_run(id) ON DELETE CASCADE,
  severity   TEXT NOT NULL,
  stage      TEXT,
  message    TEXT,
  error_json JSONB
);
CREATE INDEX idx_etl_error_log_run ON etl_error_log (etl_run_id);

COMMIT;
