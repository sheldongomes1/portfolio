#!/usr/bin/env bash
# One-time local setup: a virtual environment with Skill Gate installed, a .env for your keys,
# and the test suite run once. Safe to run again.
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
  || { echo "Skill Gate needs Python 3.11 or newer (set PYTHON=/path/to/python3.11)."; exit 1; }

[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -e ".[dev]" ruff

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env: open it and paste your ANTHROPIC_API_KEY and GEMINI_API_KEY."
fi

.venv/bin/pytest -q | tail -1

for key in ANTHROPIC_API_KEY GEMINI_API_KEY; do
  if grep -Eq "^\s*(export\s+)?${key}\s*=\s*[^[:space:]#]" .env || [ -n "${!key:-}" ]; then
    echo "${key}: set"
  else
    echo "${key}: missing (add it to .env)"
  fi
done

echo
echo "Next: . .venv/bin/activate, then run 'claude' in this folder."
