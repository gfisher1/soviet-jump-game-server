#!/usr/bin/env bash
# Runs the Soviet Jump Game backend (Linux / macOS).
#
#   ./run.sh                 # http://0.0.0.0:8080
#   HOST=0.0.0.0 PORT=8080 SJG_STATIC_SERVERS="10.0.0.5:42010:My Server" ./run.sh
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"
VENV="${VENV:-$here/.venv}"

if [[ ! -d "$VENV" ]]; then
  echo "==> Creating virtualenv ($VENV)"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet -r requirements.txt
fi

echo "==> Soviet Jump Game backend on http://$HOST:$PORT"
exec "$VENV/bin/python" -m uvicorn app.main:app --host "$HOST" --port "$PORT"
