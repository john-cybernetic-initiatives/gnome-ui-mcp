#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "The project environment is missing. Run ./scripts/bootstrap.sh first." >&2
  exit 1
fi

.venv/bin/ruff check src tests scripts mesh_authenticated_server.py mesh_local_stdio_server.py
.venv/bin/ruff format --check \
  src tests scripts mesh_authenticated_server.py mesh_local_stdio_server.py
.venv/bin/python -m pytest tests -q
.venv/bin/python scripts/verify_mesh_fork.py
