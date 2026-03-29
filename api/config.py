"""Application settings loaded from environment / .env file."""

from __future__ import annotations

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 24*60
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = "sqlite+aiosqlite:///./rpn_api.db"

    # CORS
    cors_origins: List[str] = ["*"]

    model_config = {"env_file": ".env", "env_prefix": "RPN_"}
