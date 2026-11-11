"""Database access for the pinned ECHA lists."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "reach.db"


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open the REACH database (read-only usage expected)."""
    path = Path(db_path) if db_path else DEFAULT_DB
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def list_version(conn: sqlite3.Connection) -> dict[str, str]:
    """Return pinned list versions from the metadata table."""
    return {k: v for k, v in conn.execute("SELECT key, value FROM metadata")}
