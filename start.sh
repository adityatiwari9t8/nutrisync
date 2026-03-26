#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/.nutrisync"
PID_DIR="$RUNTIME_DIR/pids"
LOG_DIR="$RUNTIME_DIR/logs"
BACKEND_DIR="$ROOT_DIR/nutrisync-backend"
FRONTEND_DIR="$ROOT_DIR/nutrisync-frontend"

mkdir -p "$PID_DIR" "$LOG_DIR"

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
REDIS_PID_FILE="$PID_DIR/redis.pid"

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
REDIS_LOG="$LOG_DIR/redis.log"

ensure_file() {
  local path="$1"
  local template="$2"
  if [[ ! -f "$path" && -f "$template" ]]; then
    cp "$template" "$path"
  fi
}

is_pid_running() {
  local pid="$1"
  [[ -n "$pid" ]] && ps -p "$pid" >/dev/null 2>&1
}

is_port_listening() {
  local port="$1"
  lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

wait_for_http() {
  local url="$1"
  local service_name="$2"
  local timeout_seconds="${3:-45}"
  local attempt=0

  until curl -fsS "$url" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if (( attempt >= timeout_seconds )); then
      echo "$service_name did not become ready in time."
      return 1
    fi
    sleep 1
  done
}

find_redis_bin() {
  local candidates=(
    "/opt/homebrew/opt/redis/bin/redis-server"
    "/usr/local/opt/redis/bin/redis-server"
  )

  local binary
  for binary in "${candidates[@]}"; do
    if [[ -x "$binary" ]]; then
      echo "$binary"
      return 0
    fi
  done

  if command -v redis-server >/dev/null 2>&1; then
    command -v redis-server
    return 0
  fi

  return 1
}

start_process() {
  local name="$1"
  local port="$2"
  local pid_file="$3"
  local log_file="$4"
  local command="$5"

  if [[ -f "$pid_file" ]]; then
    local existing_pid
    existing_pid="$(cat "$pid_file")"
    if is_pid_running "$existing_pid"; then
      echo "$name is already running with PID $existing_pid."
      return 0
    fi
    rm -f "$pid_file"
  fi

  if is_port_listening "$port"; then
    echo "$name is already listening on port $port. Leaving the existing process untouched."
    return 0
  fi

  local pid
  pid="$(
    python3 - "$log_file" "$command" <<'PY'
import subprocess
import sys

log_path = sys.argv[1]
command = sys.argv[2]

with open(log_path, "ab", buffering=0) as log_file:
    process = subprocess.Popen(
        ["bash", "-lc", command],
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    print(process.pid)
PY
  )"
  echo "$pid" >"$pid_file"
  echo "Started $name (PID $pid)."
}

ensure_file "$BACKEND_DIR/.env" "$BACKEND_DIR/.env.example"
ensure_file "$FRONTEND_DIR/.env" "$FRONTEND_DIR/.env.example"

if [[ ! -x "$BACKEND_DIR/.venv/bin/uvicorn" ]]; then
  echo "Backend virtualenv is missing. Install backend dependencies first inside $BACKEND_DIR."
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run npm install inside $FRONTEND_DIR first."
  exit 1
fi

if REDIS_BIN="$(find_redis_bin)"; then
  start_process \
    "Redis" \
    "6379" \
    "$REDIS_PID_FILE" \
    "$REDIS_LOG" \
    "cd \"$ROOT_DIR\" && exec \"$REDIS_BIN\" --save '' --appendonly no --port 6379"
else
  echo "Redis was not found on this machine. NutriSync will use its in-memory USDA cache fallback."
fi

start_process \
  "Backend" \
  "8000" \
  "$BACKEND_PID_FILE" \
  "$BACKEND_LOG" \
  "cd \"$BACKEND_DIR\" && if [[ -f .env ]]; then set -a && source .env && set +a; fi && exec .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000"

wait_for_http "http://127.0.0.1:8000/health" "Backend"

start_process \
  "Frontend" \
  "5173" \
  "$FRONTEND_PID_FILE" \
  "$FRONTEND_LOG" \
  "cd \"$FRONTEND_DIR\" && exec npm run dev -- --host 127.0.0.1 --port 5173"

wait_for_http "http://127.0.0.1:5173" "Frontend"

echo
echo "NutriSync is running."
echo "Frontend: http://127.0.0.1:5173"
echo "Backend:  http://127.0.0.1:8000"
echo "Logs:     $LOG_DIR"
