#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "The project environment is missing. Run ./scripts/bootstrap.sh first." >&2
  exit 1
fi

UV_NO_MANAGED_PYTHON=1 uv pip install \
  --python "$PROJECT_ROOT/.venv/bin/python" \
  --requirement requirements/mesh-capabilities.txt
