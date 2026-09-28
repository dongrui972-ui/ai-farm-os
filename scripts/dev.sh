#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/start-api.sh" &
API_PID=$!
cleanup() {
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT
echo "等待 API 就绪 http://127.0.0.1:8000/api/health"
for _ in $(seq 1 40); do
  if curl -sf http://127.0.0.1:8000/api/health >/dev/null; then
    echo "API 已就绪"
    break
  fi
  sleep 0.4
done
"$ROOT/scripts/start-web.sh"
