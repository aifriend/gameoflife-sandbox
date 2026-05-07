#!/usr/bin/env bash
# Launch the Life Studio web frontend.
#
# What it does:
#   1. Checks whether the chosen port is in use; offers to kill the
#      process if it's a stale http.server we started before.
#   2. Starts `python -m http.server` pointing at web/.
#   3. Opens the URL in your default browser (macOS / Linux).
#   4. Tails the server access log so you can see requests as you click
#      around. Ctrl+C stops the server cleanly.
#
# Usage:
#   ./scripts/launch_web.sh              # default port 5173
#   ./scripts/launch_web.sh 8080         # custom port
#   PORT=4000 ./scripts/launch_web.sh    # via env var

set -euo pipefail

PORT="${1:-${PORT:-5173}}"
HOST="${HOST:-127.0.0.1}"

# Resolve project root from this script's location, regardless of CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WEB="$ROOT/web"
LOG="$ROOT/.web-server.log"
PID_FILE="$ROOT/.web-server.pid"

# tput colors are nicer than raw escapes; degrade gracefully if no tty
if [[ -t 1 ]]; then
  C_INFO=$'\033[36m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_DIM=$'\033[2m'; C_END=$'\033[0m'
else
  C_INFO=""; C_OK=""; C_WARN=""; C_ERR=""; C_DIM=""; C_END=""
fi

say()  { printf '%s[life]%s %s\n' "$C_INFO" "$C_END" "$*"; }
ok()   { printf '%s[life]%s %s%s%s\n' "$C_INFO" "$C_END" "$C_OK"   "$*" "$C_END"; }
warn() { printf '%s[life]%s %s%s%s\n' "$C_INFO" "$C_END" "$C_WARN" "$*" "$C_END"; }
die()  { printf '%s[life]%s %s%s%s\n' "$C_INFO" "$C_END" "$C_ERR"  "$*" "$C_END" >&2; exit 1; }

# ----------------------------------------------------------------- preflight
[[ -d "$WEB" ]]            || die "web/ directory not found at $WEB"
[[ -f "$WEB/index.html" ]] || die "web/index.html missing — has the frontend been built?"
command -v python3 >/dev/null || die "python3 not found on PATH"

# ------------------------------------------------------------ port hygiene
say "Checking port $PORT…"
if EXISTING_PID="$(lsof -tiTCP:"$PORT" -sTCP:LISTEN 2>/dev/null)" && [[ -n "$EXISTING_PID" ]]; then
  EXISTING_CMD="$(ps -p "$EXISTING_PID" -o command= 2>/dev/null || true)"
  warn "Port $PORT is in use by PID $EXISTING_PID:"
  printf '       %s\n' "$EXISTING_CMD"

  # Auto-kill only if it looks like our previous http.server for THIS web/ dir
  if [[ "$EXISTING_CMD" == *"http.server"* && "$EXISTING_CMD" == *"$WEB"* ]]; then
    say "Looks like a previous launch_web.sh — killing it…"
    kill -TERM "$EXISTING_PID" 2>/dev/null || true
    sleep 0.5
    kill -KILL "$EXISTING_PID" 2>/dev/null || true
    ok "Cleared port $PORT"
  else
    die "Port $PORT belongs to something else. Pick another with: $0 <port>"
  fi
else
  ok "Port $PORT is free"
fi

# ------------------------------------------------------------ cleanup hook
cleanup() {
  echo
  if [[ -f "$PID_FILE" ]]; then
    SVR_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "${SVR_PID:-}" ]] && kill -0 "$SVR_PID" 2>/dev/null; then
      say "Stopping server (PID $SVR_PID)…"
      kill -TERM "$SVR_PID" 2>/dev/null || true
      sleep 0.3
      kill -KILL "$SVR_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
  fi
  ok "Stopped. Server log preserved at $LOG"
}
trap cleanup INT TERM EXIT

# --------------------------------------------------------------- run server
: > "$LOG"
say "Starting http.server on $HOST:$PORT (root: web/)…"
python3 -u -m http.server "$PORT" --bind "$HOST" --directory "$WEB" \
  >>"$LOG" 2>&1 &
SVR_PID=$!
echo "$SVR_PID" > "$PID_FILE"

# Wait for the server to bind (max 5s)
for _ in {1..50}; do
  if curl -fsS "http://$HOST:$PORT/index.html" >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done
if ! curl -fsS "http://$HOST:$PORT/index.html" >/dev/null 2>&1; then
  die "Server failed to start within 5s. See $LOG"
fi
ok "Server up at http://$HOST:$PORT/  (PID $SVR_PID)"

# --------------------------------------------------------------- open client
URL="http://$HOST:$PORT/"
if command -v open >/dev/null 2>&1; then
  open "$URL"             # macOS
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 &   # Linux
elif command -v wslview >/dev/null 2>&1; then
  wslview "$URL" >/dev/null 2>&1 &    # WSL
else
  warn "Couldn't auto-open a browser. Visit $URL manually."
fi
ok "Browser launched → $URL"

# ----------------------------------------------------------------- tail log
echo
say "Tailing server log. ${C_DIM}Ctrl+C to stop.${C_END}"
echo "─────────────────────────────────────────────────────────────"
tail -F "$LOG"
