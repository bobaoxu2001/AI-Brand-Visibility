"""Environment-backed configuration helpers for pipeline scripts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _to_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    db_path: Path
    openai_api_key: str | None
    anthropic_api_key: str | None
    openai_model: str
    anthropic_model: str
    max_concurrency: int
    request_delay_seconds: float
    max_retries: int


def get_settings() -> Settings:
    db_path_raw = os.getenv("DB_PATH", "visibility_data.db")
    db_path = Path(db_path_raw)
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    return Settings(
        db_path=db_path,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
        max_concurrency=max(1, _to_int(os.getenv("MAX_CONCURRENCY", "5"), 5)),
        request_delay_seconds=max(
            0.0, _to_float(os.getenv("REQUEST_DELAY_SECONDS", "0.25"), 0.25)
        ),
        max_retries=max(1, _to_int(os.getenv("MAX_RETRIES", "3"), 3)),
    )


def validate_required_env(var_names: list[str]) -> None:
    missing = [name for name in var_names if not os.getenv(name)]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variables: {joined}. "
            "Create a .env file (you can copy from .env.example) and set them."
        )
