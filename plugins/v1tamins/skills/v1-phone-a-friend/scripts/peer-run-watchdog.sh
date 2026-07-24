#!/usr/bin/env bash
# Deadline watchdog for a recorded peer. Honors peer.session for PGID kill.
# Args: seconds donefile pidfile childpidfile sessfile

set -u

seconds="$1"
donefile="$2"
pidfile="$3"
childpidfile="$4"
sessfile="$5"

sleep "$seconds"
[ -f "$donefile" ] && exit 0

target="$(sed -n '1p' "$pidfile" 2>/dev/null || true)"
child="$(sed -n '1p' "$childpidfile" 2>/dev/null || true)"
sess="$(cat "$sessfile" 2>/dev/null || printf '0')"

case "$target" in
  ''|*[!0-9]*) exit 0 ;;
esac

if [ "$sess" = "1" ]; then
  kill -TERM -- "-$target" 2>/dev/null || true
fi
case "$child" in
  ''|*[!0-9]*) ;;
  *) kill -TERM "$child" 2>/dev/null || true ;;
esac
case "$target" in
  ''|*[!0-9]*) ;;
  *) kill -TERM "$target" 2>/dev/null || true ;;
esac

sleep 1

if [ "$sess" = "1" ]; then
  kill -KILL -- "-$target" 2>/dev/null || true
fi
case "$child" in
  ''|*[!0-9]*) ;;
  *) kill -KILL "$child" 2>/dev/null || true ;;
esac
case "$target" in
  ''|*[!0-9]*) ;;
  *) kill -KILL "$target" 2>/dev/null || true ;;
esac
