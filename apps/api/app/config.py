"""Runtime configuration from environment. Secrets never live in the repo."""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://aduana:aduana@localhost:5432/aduanamap")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    banxico_token: str = os.getenv("BANXICO_TOKEN", "")
    banxico_fix_serie: str = os.getenv("BANXICO_FIX_SERIE", "SF43718")
    version: str = "0.1.0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
