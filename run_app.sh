#!/usr/bin/env bash
# Khởi động SRT Whiteboard Studio (giao diện PySide6)
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/app/launch.py" "$@"
