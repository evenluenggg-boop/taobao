"""SQLite database initialization helpers for taobao-collector."""

from __future__ import annotations

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "taobao_collector.sqlite3"


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> Path:
    """Create or update a SQLite database using the project schema.

    Parameters:
        database_path: Target SQLite file path. Parent directories are created.
        schema_path: SQL schema file to execute.

    Returns:
        The resolved database path.
    """

    database_path = Path(database_path)
    schema_path = Path(schema_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = schema_path.read_text(encoding="utf-8")
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_sql)

    return database_path
