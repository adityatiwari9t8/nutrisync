#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT_DIR/.nutrisync/pids"

stop_process() {
  local name="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$name was not started by this script."
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"

  if ps -p "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    for _ in {1..10}; do
      if ! ps -p "$pid" >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    if ps -p "$pid" >/dev/null 2>&1; then
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
    echo "Stopped $name (PID $pid)."
  else
    echo "$name PID file existed, but the process was already gone."
  fi

  rm -f "$pid_file"
}

stop_process "Frontend" "$PID_DIR/frontend.pid"
stop_process "Backend" "$PID_DIR/backend.pid"
stop_process "Redis" "$PID_DIR/redis.pid"
