#!/usr/bin/env bash
# Shared helpers for peer-run.sh and peer-run-watchdog.sh.
# Sourced only; not executed directly.

peer_alive() {
  local pid="$1"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

peer_read_number() {
  local file="$1"
  local value=""
  [ -f "$file" ] && value="$(sed -n '1p' "$file")"
  case "$value" in
    ''|*[!0-9]*) printf '\n' ;;
    *) printf '%s\n' "$value" ;;
  esac
}

# Terminate recorded peer processes by PID/PGID only.
# Args: pidfile childpidfile sessfile [grace_iterations]
# Does not touch a watchdog process; callers that own the watchdog kill it first.
terminate_peer_processes() {
  local pidfile="$1"
  local childpidfile="$2"
  local sessfile="$3"
  local grace="${4:-10}"
  local pid cpid sess killed="" i

  pid="$(peer_read_number "$pidfile")"
  cpid="$(peer_read_number "$childpidfile")"
  sess="$(cat "$sessfile" 2>/dev/null || printf '0')"

  if [ "$sess" = "1" ] && [ -n "$pid" ]; then
    if kill -TERM -- "-$pid" 2>/dev/null; then
      killed="pgid=$pid"
    fi
  fi
  for target in "$cpid" "$pid"; do
    if peer_alive "$target"; then
      kill -TERM "$target" 2>/dev/null || true
      killed="${killed:+$killed }pid=$target"
    fi
  done

  i=0
  while [ "$i" -lt "$grace" ]; do
    if ! peer_alive "$pid" && ! peer_alive "$cpid"; then
      break
    fi
    sleep 0.1
    i=$((i + 1))
  done

  if [ "$sess" = "1" ] && [ -n "$pid" ] && peer_alive "$pid"; then
    kill -KILL -- "-$pid" 2>/dev/null || true
  fi
  for target in "$cpid" "$pid"; do
    if peer_alive "$target"; then
      kill -KILL "$target" 2>/dev/null || true
    fi
  done
  printf '%s\n' "$killed"
}
