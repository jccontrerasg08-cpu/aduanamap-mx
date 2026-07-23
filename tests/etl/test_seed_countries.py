"""seed_countries: extracts real countries from the built GeoJSON, skips neutrals."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest  # noqa: E402

from workers import seed_countries  # noqa: E402

pytestmark = pytest.mark.skipif(
    not seed_countries.GEOJSON.exists(),
    reason="countries-50m.geojson no generado (tools/map-build)",
)


def test_rows_extracts_countries_and_skips_neutrals():
    rows = seed_countries._rows()
    # Every row is (iso2, iso3, name_es, name_en, region, subregion).
    assert all(len(r) == 6 for r in rows)
    iso3s = {r[1] for r in rows}
    # The ISO_A3=-99 casualties must be present (numeric join, ADR 0004).
    assert {"FRA", "NOR", "MEX", "USA"} <= iso3s
    # Neutral features (Kosovo etc.) carry iso3=null and must be excluded.
    assert None not in iso3s
    assert len(rows) > 190  # ~236 UN countries


def test_mexico_has_bilingual_names():
    rows = seed_countries._rows()
    mex = next(r for r in rows if r[1] == "MEX")
    iso2, iso3, name_es, name_en, region, _sub = mex
    assert iso2 == "MX"
    assert name_es == "México" and name_en == "Mexico"
    assert region == "Americas"
