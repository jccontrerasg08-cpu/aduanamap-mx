"""Source preservation + trazabilidad primitives shared by every ETL worker.

Pipeline discipline (report §Pipeline ETL):
  capture -> preserve (raw snapshot + SHA-256) -> parse -> normalize -> publish

Preserving the raw artifact matters as much as the final table: a change in
HTML/XLSX/PDF can break the parser without changing the legal content.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

RAW_DIR = Path(os.getenv("DATA_RAW_DIR", "data/raw"))
SNAPSHOT_DIR = Path(os.getenv("DATA_SNAPSHOT_DIR", "data/snapshots"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


@dataclass
class Snapshot:
    source_name: str
    source_url: str
    sha256: str
    storage_key: str
    fetched_at: datetime
    content_type: str


def preserve(source_name: str, source_url: str, payload: bytes,
             content_type: str, parser_version: str) -> Snapshot:
    """Write the raw artifact to disk keyed by content hash and return metadata.

    Object storage (S3/MinIO) is the production target; local disk here keeps the
    worker runnable without external infra. The SHA-256 is the dedupe/versioning key.
    """
    digest = sha256_bytes(payload)
    fetched_at = datetime.now(timezone.utc)
    day = fetched_at.strftime("%Y/%m/%d")
    dest = SNAPSHOT_DIR / source_name / day / f"{digest}.raw"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    return Snapshot(
        source_name=source_name,
        source_url=source_url,
        sha256=digest,
        storage_key=str(dest),
        fetched_at=fetched_at,
        content_type=content_type,
    )
