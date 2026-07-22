"""Runtime configuration from environment. Secrets never live in the repo.

Settings are validated once at startup. `startup_warnings()` surfaces
misconfiguration (e.g. a Banxico token that is not 64 chars) without crashing
the process — the API must still boot and degrade gracefully.
"""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, Field

BANXICO_TOKEN_LEN = 64


class Settings(BaseModel):
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    database_url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "postgresql://aduana:aduana@localhost:5432/aduanamap"
        )
    )
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    banxico_token: str = Field(default_factory=lambda: os.getenv("BANXICO_TOKEN", ""))
    banxico_fix_serie: str = Field(default_factory=lambda: os.getenv("BANXICO_FIX_SERIE", "SF43718"))
    cors_origins: str = Field(default_factory=lambda: os.getenv("APP_BASE_URL", "*"))
    rate_limit_enabled: bool = Field(
        default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "1") not in {"0", "false", "False"}
    )
    version: str = "0.1.0"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @property
    def cors_allow_origins(self) -> list[str]:
        if self.cors_origins.strip() in {"", "*"}:
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def startup_warnings(self) -> list[str]:
        w: list[str] = []
        if not self.banxico_token:
            w.append("BANXICO_TOKEN no configurado: /api/banxico/* servirá snapshot o 'no disponible'.")
        elif len(self.banxico_token) != BANXICO_TOKEN_LEN:
            w.append(
                f"BANXICO_TOKEN tiene {len(self.banxico_token)} caracteres; "
                f"el token oficial del SIE tiene {BANXICO_TOKEN_LEN}."
            )
        if self.is_production and self.cors_allow_origins == ["*"]:
            w.append("CORS abierto a '*' en producción: define APP_BASE_URL con orígenes explícitos.")
        return w


@lru_cache
def get_settings() -> Settings:
    return Settings()
