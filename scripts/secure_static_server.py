#!/usr/bin/env python3
"""Serve Telegram Mini App artifacts from this git repo safely.

Intended to be used behind Cloudflare Tunnel. It serves only a small allowlist
of public artifact paths and blocks dotfiles / traversal / arbitrary repo files.
"""
from __future__ import annotations

import argparse
import mimetypes
import os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlparse

ALLOWED_EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".svg",
    ".gif",
    ".ico",
    ".txt",
}

BLOCKED_NAMES = {
    ".git",
    ".env",
    ".DS_Store",
    "node_modules",
    "worker",
    "scripts",
}


def is_safe_relative_path(raw_path: str) -> bool:
    decoded = unquote(raw_path)
    if "\x00" in decoded:
        return False
    if decoded in ("/", ""):
        return True
    parts = [p for p in decoded.strip("/").split("/") if p]
    if not parts:
        return True
    for part in parts:
        if part in (".", "..") or part.startswith(".") or part in BLOCKED_NAMES:
            return False
    suffix = Path(parts[-1]).suffix.lower()
    return suffix in ALLOWED_EXTENSIONS


class Handler(BaseHTTPRequestHandler):
    server_version = "AgentMiniAppSecureStatic/1.0"

    def log_message(self, fmt: str, *args):
        print(f"{self.address_string()} - {fmt % args}")

    def do_GET(self):
        self._serve(head_only=False)

    def do_HEAD(self):
        self._serve(head_only=True)

    def _serve(self, head_only: bool):
        parsed = urlparse(self.path)
        path = parsed.path

        if not is_safe_relative_path(path):
            self._send_text(404, "Not found", head_only)
            return

        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        root = self.server.root  # type: ignore[attr-defined]
        target = (root / rel).resolve()

        try:
            target.relative_to(root)
        except ValueError:
            self._send_text(404, "Not found", head_only)
            return

        if not target.is_file():
            self._send_text(404, "Not found", head_only)
            return

        ctype, _ = mimetypes.guess_type(str(target))
        if ctype is None:
            ctype = "application/octet-stream"
        if target.suffix.lower() == ".html":
            ctype = "text/html; charset=utf-8"
        elif target.suffix.lower() in {".js", ".mjs"}:
            ctype = "application/javascript; charset=utf-8"
        elif target.suffix.lower() == ".css":
            ctype = "text/css; charset=utf-8"
        elif target.suffix.lower() == ".json":
            ctype = "application/json; charset=utf-8"

        data = target.read_bytes()
        self.send_response(200)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(data)))
        self.send_header("cache-control", "no-store, max-age=0")
        self.send_header("x-miniapp-local", "true")
        self.end_headers()
        if not head_only:
            self.wfile.write(data)

    def _send_text(self, status: int, text: str, head_only: bool):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/plain; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.send_header("cache-control", "no-store, max-age=0")
        self.end_headers()
        if not head_only:
            self.wfile.write(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8788)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.root = root  # type: ignore[attr-defined]
    print(f"Serving {root} on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
