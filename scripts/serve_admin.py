#!/usr/bin/env python3
"""Run the FastAPI local web backend."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the Taobao 5-shop data analysis system.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind. Defaults to 8000.")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload for local development.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uvicorn.run("taobao_collector.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
