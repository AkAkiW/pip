#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ "${1:-}" = "test" ]; then
    exec python3 -m unittest discover -s tests -t . -v
fi
exec python3 -m src.main "$@"
