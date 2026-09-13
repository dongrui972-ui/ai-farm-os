#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/start-api.sh" &
API_PID=$!
trap 'kill $API_PID' EXIT
"$ROOT/scripts/start-web.sh"
