#!/usr/bin/env python3
"""Serve the static local admin homepage."""

from __future__ import annotations

import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = PROJECT_ROOT / "web"


class AdminRequestHandler(SimpleHTTPRequestHandler):
    """Serve the admin homepage at `/` while exposing static project templates."""

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            self.path = "/web/index.html"
        super().do_GET()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the taobao-collector local admin page.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind. Defaults to 8000.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    handler = functools.partial(AdminRequestHandler, directory=str(PROJECT_ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving local admin homepage at http://{args.host}:{args.port}/")
    print(f"Static files are served from: {WEB_ROOT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local admin server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
