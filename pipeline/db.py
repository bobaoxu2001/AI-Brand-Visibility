"""SQLite helpers for the AI brand visibility tracker."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from pipeline.config import get_settings


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    settings = get_settings()
    resolved_db_path = db_path or settings.db_path
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(resolved_db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            prompt_text TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS raw_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            raw_text TEXT,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'success',
            error_message TEXT,
            UNIQUE(prompt_id, model_name),
            FOREIGN KEY(prompt_id) REFERENCES prompts(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS parsed_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            response_id INTEGER NOT NULL UNIQUE,
            top_brand TEXT NOT NULL,
            sentiment REAL NOT NULL CHECK(sentiment >= -1.0 AND sentiment <= 1.0),
            key_features TEXT NOT NULL,
            FOREIGN KEY(response_id) REFERENCES raw_responses(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_prompts_category
            ON prompts(category);
        CREATE INDEX IF NOT EXISTS idx_raw_responses_prompt_id
            ON raw_responses(prompt_id);
        CREATE INDEX IF NOT EXISTS idx_raw_responses_model_name
            ON raw_responses(model_name);
        CREATE INDEX IF NOT EXISTS idx_parsed_metrics_response_id
            ON parsed_metrics(response_id);
        """
    )
    conn.commit()


def prompt_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS total FROM prompts").fetchone()
    return int(row["total"])


def reset_prompt_related_tables(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM parsed_metrics")
    conn.execute("DELETE FROM raw_responses")
    conn.execute("DELETE FROM prompts")
    conn.commit()


def insert_prompts(
    conn: sqlite3.Connection, prompts: Iterable[tuple[str, str]]
) -> None:
    conn.executemany(
        """
        INSERT INTO prompts (category, prompt_text)
        VALUES (?, ?)
        """,
        list(prompts),
    )
    conn.commit()


def fetch_prompts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, category, prompt_text FROM prompts ORDER BY id"
    ).fetchall()


def upsert_raw_response(
    conn: sqlite3.Connection,
    prompt_id: int,
    model_name: str,
    raw_text: str | None,
    *,
    status: str = "success",
    error_message: str | None = None,
    timestamp: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO raw_responses (
            prompt_id,
            model_name,
            raw_text,
            timestamp,
            status,
            error_message
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(prompt_id, model_name) DO UPDATE SET
            raw_text = excluded.raw_text,
            timestamp = excluded.timestamp,
            status = excluded.status,
            error_message = excluded.error_message
        """,
        (
            prompt_id,
            model_name,
            raw_text,
            timestamp or utc_now_iso(),
            status,
            error_message,
        ),
    )
    conn.commit()


def category_breakdown(conn: sqlite3.Connection) -> Sequence[sqlite3.Row]:
    return conn.execute(
        """
        SELECT category, COUNT(*) AS total
        FROM prompts
        GROUP BY category
        ORDER BY category
        """
    ).fetchall()
