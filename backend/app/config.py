"""
config.py
─────────
Application settings loaded from environment variables / .env file.
Uses Pydantic BaseSettings for automatic type-coercion and validation.

Usage
-----
    from backend.app.config import settings

    print(settings.DATABASE_URL)
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration is read from environment variables.
    A .env file in the project root is loaded automatically.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite:///./jee_dropout.db",
        description="SQLAlchemy connection string. "
                    "Use postgresql+psycopg2://... for production.",
    )

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-USE-OPENSSL-RAND-HEX-32",
        description="HS256 signing key. Must be overridden in production.",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── ML models ─────────────────────────────────────────────────────────────
    MODEL_DIR: str = Field(
        default="models",
        description="Directory containing the trained .pkl artefacts.",
    )

    # ── Application ───────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "JEE Dropout Prediction API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins (frontend dev servers).",
    )

    # ── Prediction defaults ───────────────────────────────────────────────────
    PREDICTION_THRESHOLD: float = 0.35
    MIN_DATA_FOR_PREDICTION: int = 1   # minimum mock tests required

    # ── Email (SMTP) ───────────────────────────────────────────────────────────
    # Leave blank to disable email sending (graceful no-op)
    SMTP_HOST:     str = Field(default="", description="SMTP server hostname")
    SMTP_PORT:     int = Field(default=587,  description="SMTP port (587=TLS, 465=SSL)")
    SMTP_USER:     str = Field(default="", description="SMTP login username")
    SMTP_PASSWORD: str = Field(default="", description="SMTP login password")

    # ── Institute ──────────────────────────────────────────────────────────────
    INSTITUTE_NAME: str = Field(default="JEE Coaching Institute", description="Shown in PDF reports")

    @field_validator("SECRET_KEY")
    @classmethod
    def warn_insecure_key(cls, v: str) -> str:
        if v.startswith("CHANGE-ME"):
            import warnings
            warnings.warn(
                "SECRET_KEY is using the insecure default. "
                "Set a strong SECRET_KEY in your .env file.",
                stacklevel=2,
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton."""
    return Settings()


# Module-level singleton for convenience imports
settings: Settings = get_settings()
