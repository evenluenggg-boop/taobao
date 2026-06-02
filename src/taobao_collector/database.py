"""SQLite database helpers for the Taobao 5-shop import system."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "local" / "taobao_5shop.db"

CUSTOMER_SERVICE_METRICS_OPTIONAL_COLUMNS = {
    "wangwang_nick_raw": "TEXT",
    "effective_reception_count": "INTEGER",
    "inquiry_count": "INTEGER",
    "order_buyer_count": "INTEGER",
    "order_amount": "REAL",
    "sales_buyer_count": "INTEGER",
    "sales_amount": "REAL",
    "sales_quantity": "INTEGER",
    "order_count": "INTEGER",
    "personal_sales_ratio": "REAL",
    "refund_amount": "REAL",
    "net_sales_amount": "REAL",
    "wangwang_type": "TEXT",
}

ALLOWED_TABLES = {
    "customer_questions",
    "products",
    "aftersales",
    "shops",
    "daily_reports",
    "customer_service_metrics",
}


def ensure_optional_columns(
    connection: sqlite3.Connection,
    table_name: str,
    optional_columns: dict[str, str],
) -> None:
    """Add optional columns to existing local SQLite tables when upgrading schema."""

    existing_columns = {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for column_name, column_type in optional_columns.items():
        if column_name not in existing_columns:
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


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
        ensure_optional_columns(
            connection,
            "customer_service_metrics",
            CUSTOMER_SERVICE_METRICS_OPTIONAL_COLUMNS,
        )

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

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unsupported table: {table_name}")

    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def count_rows(table_name: str) -> int:
    """Count rows in a known table."""

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Unsupported table: {table_name}")

    with get_connection() as connection:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
