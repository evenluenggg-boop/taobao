"""SQLite database helpers for the Taobao 5-shop import system."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "local" / "taobao_5shop.db"


def initialize_database(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
    schema_path: str | Path = DEFAULT_SCHEMA_PATH,
) -> Path:
    """Create or update a SQLite database using the project schema."""

    database_path = Path(database_path)
    schema_path = Path(schema_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = schema_path.read_text(encoding="utf-8")
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_sql)

    return database_path


def get_connection(database_path: str | Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Return a SQLite connection with rows addressable by column name."""

    initialize_database(database_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def fetch_rows(table_name: str, limit: int = 50) -> list[dict[str, Any]]:
    """Fetch preview rows from a known table."""

    allowed_tables = {
        "customer_questions",
        "products",
        "aftersales",
        "shops",
        "daily_reports",
        "customer_service_metrics",
    }
    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table: {table_name}")

    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def count_rows(table_name: str) -> int:
    """Count rows in a known table."""

    allowed_tables = {
        "customer_questions",
        "products",
        "aftersales",
        "shops",
        "daily_reports",
        "customer_service_metrics",
    }
    if table_name not in allowed_tables:
        raise ValueError(f"Unsupported table: {table_name}")

    with get_connection() as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
