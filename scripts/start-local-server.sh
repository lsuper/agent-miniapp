#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/secure_static_server.py --root "$PWD" --host 127.0.0.1 --port "${PORT:-8788}"
