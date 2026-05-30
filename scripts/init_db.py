#!/usr/bin/env python3
"""Initialize the local SQLite database for development."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from taobao_collector.database import DEFAULT_DATABASE_PATH, initialize_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize taobao-collector SQLite database.")
    parser.add_argument(
        "--database",
        default=str(DEFAULT_DATABASE_PATH),
        help="SQLite database path. Defaults to data/local/taobao_5shop.db.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_path = initialize_database(Path(args.database))
    print(f"Initialized database: {database_path}")


if __name__ == "__main__":
    main()
