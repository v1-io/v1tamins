#!/usr/bin/env bash
# peer-run.sh — launch and supervise one detached peer process.
#
# The caller supplies a complete provider wrapper. This helper owns stdin
# closure, detached sessions, bounded deadlines, sentinels, typed verdicts,
# and PID/PGID-scoped teardown. It never searches for or kills a command-line
# pattern. status and verdict are pure observation; watchdog and teardown own
# mutation.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INNER="$SCRIPT_DIR/peer-run-inner.sh"
WATCHDOG="$SCRIPT_DIR/peer-run-watchdog.sh"
# shellcheck source=peer-run-lib.sh
. "$SCRIPT_DIR/peer-run-lib.sh"

die() {
  printf 'peer-run: %s\n' "$1" >&2
  exit "${2:-2}"
}

usage() {
  cat >&2 <<'EOF'
Usage:
  peer-run.sh launch   --dir <run-dir> --slug <slug> [--deadline-seconds <n>] -- <command...>
  peer-run.sh status   --dir <run-dir> --slug <slug>
  peer-run.sh verdict  --dir <run-dir> --slug <slug> [--json]
  peer-run.sh teardown --dir <run-dir> --slug <slug>

States: running | complete | empty_output | stalled | timed_out
EOF
}

cmd="${1:-}"
[ -n "$cmd" ] || { usage; exit 2; }
shift || true

RUNDIR=""
SLUG=""
DEADLINE_SECONDS=""
JSON=false
PEER_CMD=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir)
      [ "$#" -ge 2 ] || die "--dir needs a value"
      RUNDIR="$2"
      shift 2
      ;;
    --slug)
      [ "$#" -ge 2 ] || die "--slug needs a value"
      SLUG="$2"
      shift 2
      ;;
    --deadline-seconds)
      [ "$#" -ge 2 ] || die "--deadline-seconds needs a value"
      DEADLINE_SECONDS="$2"
      shift 2
      ;;
    --json)
      JSON=true
      shift
      ;;
    --)
      shift
      PEER_CMD=("$@")
      break
      ;;
    *)
      die "unexpected argument: $1"
      ;;
  esac
done

[ -n "$RUNDIR" ] || die "--dir is required"
[ -n "$SLUG" ] || die "--slug is required"
case "$SLUG" in
  *[!A-Za-z0-9._-]*) die "slug must contain only letters, numbers, dot, underscore, and hyphen" ;;
esac

case "$cmd" in
  launch)
    [ "${#PEER_CMD[@]}" -gt 0 ] || die "launch needs: -- <peer-command...>"
    [ -n "$DEADLINE_SECONDS" ] || DEADLINE_SECONDS="${PEER_RUN_DEADLINE_SECONDS:-900}"
    case "$DEADLINE_SECONDS" in
      ''|*[!0-9]*) die "deadline must be a positive number of seconds" ;;
      0) die "deadline must be greater than zero" ;;
    esac
    ;;
  *)
    [ -z "$DEADLINE_SECONDS" ] || die "--deadline-seconds is valid only for launch"
    ;;
esac

peerdir="$RUNDIR/$SLUG"
pidfile="$peerdir/peer.pid"
childpidfile="$peerdir/peer.child.pid"
sessfile="$peerdir/peer.session"
donefile="$peerdir/peer.done"
deadlinefile="$peerdir/peer.deadline"
watchdogfile="$peerdir/peer.watchdog.pid"
outfile="$peerdir/peer.stdout"
errfile="$peerdir/peer.stderr"

bytes() {
  if [ -f "$1" ]; then
    wc -c < "$1" | tr -d ' '
  else
    printf '0\n'
  fi
}

has_content() {
  [ -s "$1" ] && LC_ALL=C grep -q '[^[:space:]]' "$1" 2>/dev/null
}

# Plain text: any non-whitespace is enough. JSON / stream-json / --json: require a
# terminal answer payload, not framing, progress, or error-only events.
has_peer_answer() {
  local path="$1"
  has_content "$path" || return 1
  python3 - "$path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="replace")
stripped = text.strip()
if not stripped:
    raise SystemExit(1)

def text_blocks(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.strip():
                return True
            if isinstance(item, dict):
                if item.get("type") == "text" and text_blocks(item.get("text")):
                    return True
                if text_blocks(item.get("text")) or text_blocks(item.get("content")):
                    return True
    if isinstance(value, dict):
        return text_blocks(value.get("text")) or text_blocks(value.get("content"))
    return False


def is_terminal_answer(obj) -> bool:
    if not isinstance(obj, dict):
        return False
    if obj.get("is_error") is True:
        return False
    typ = str(obj.get("type") or obj.get("event") or "").lower()
    if typ in {
        "system",
        "status",
        "progress",
        "ping",
        "heartbeat",
        "tool_progress",
        "user",
        "rate_limit_event",
    }:
        return False
    subtype = str(obj.get("subtype") or "").lower()
    if subtype in {"error", "failure", "failed"}:
        return False
    if typ == "result":
        return text_blocks(obj.get("result"))
    for key in ("result", "message", "text", "content", "output", "response"):
        if key in obj and text_blocks(obj.get(key)):
            if typ in {
                "",
                "result",
                "message",
                "assistant",
                "agent_message",
                "response",
                "item.completed",
                "agent.completed",
            }:
                return True
            if typ.startswith("item.") and "completed" in typ:
                return True
    return False


objects: list[object] = []
json_lines = 0
nonempty = 0
for line in text.splitlines():
    line = line.strip()
    if not line:
        continue
    nonempty += 1
    try:
        objects.append(json.loads(line))
        json_lines += 1
    except json.JSONDecodeError:
        objects.append(None)

if nonempty and json_lines == nonempty:
    raise SystemExit(0 if any(is_terminal_answer(obj) for obj in objects) else 1)

try:
    payload = json.loads(stripped)
except json.JSONDecodeError:
    # Plain text with non-whitespace content.
    raise SystemExit(0)

if isinstance(payload, list):
    raise SystemExit(0 if any(is_terminal_answer(obj) for obj in payload) else 1)
raise SystemExit(0 if is_terminal_answer(payload) else 1)
PY
}

deadline_expired() {
  local deadline
  deadline="$(peer_read_number "$deadlinefile")"
  [ -n "$deadline" ] || return 1
  [ "$(date +%s)" -ge "$deadline" ]
}

terminate_recorded() {
  local watchdog
  watchdog="$(peer_read_number "$watchdogfile")"
  if peer_alive "$watchdog"; then
    kill -TERM "$watchdog" 2>/dev/null || true
  fi
  terminate_peer_processes "$pidfile" "$childpidfile" "$sessfile" 10
}

resolve_state() {
  local cpid lpid
  cpid="$(peer_read_number "$childpidfile")"
  lpid="$(peer_read_number "$pidfile")"

  # A done sentinel is the terminal boundary. Zombie wrappers can still answer
  # kill -0, so never treat "alive" as stronger than a recorded exit.
  if [ -f "$donefile" ]; then
    if has_peer_answer "$outfile"; then
      printf 'complete\n'
      return 0
    fi
    printf 'empty_output\n'
    return 1
  fi

  if deadline_expired; then
    if peer_alive "$cpid" || peer_alive "$lpid"; then
      printf 'timed_out\n'
      return 1
    fi
    # Deadline passed, process gone, no done sentinel: interrupted/stalled.
    printf 'timed_out\n'
    return 1
  fi

  if peer_alive "$cpid" || peer_alive "$lpid"; then
    printf 'running\n'
    return 2
  fi

  # Content without a done sentinel is an interrupted recorder, not complete.
  printf 'stalled\n'
  return 1
}

json_number_or_null() {
  case "$1" in
    ''|\?) printf 'null' ;;
    *[!0-9-]*) printf 'null' ;;
    *) printf '%s' "$1" ;;
  esac
}

case "$cmd" in
  launch)
    [ -x "$INNER" ] || die "missing executable peer-run-inner.sh"
    [ -x "$WATCHDOG" ] || die "missing executable peer-run-watchdog.sh"
    mkdir -p "$peerdir" || die "cannot create run directory"
    # Reusing a slug must not leave a prior watchdog/peer to kill the new run.
    if [ -f "$pidfile" ] || [ -f "$watchdogfile" ] || [ -f "$childpidfile" ]; then
      terminate_recorded >/dev/null || true
    fi
    : > "$outfile"
    : > "$errfile"
    rm -f "$pidfile" "$sessfile" "$donefile" "$childpidfile" "$watchdogfile"
    deadline_epoch=$(( $(date +%s) + DEADLINE_SECONDS ))
    printf '%s\n' "$deadline_epoch" > "$deadlinefile"

    # The inner runner records its own PID because GNU setsid may fork before
    # exec. The shell that writes this file is the real session leader.
    # Prefer true session detach: setsid, then Perl POSIX::setsid on hosts
    # without setsid (notably macOS), else best-effort nohup.
    if command -v setsid >/dev/null 2>&1; then
      setsid "$INNER" "$pidfile" "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" &
      launcher_pid=$!
      sess=1
      how="setsid"
    elif command -v perl >/dev/null 2>&1; then
      perl -e 'use POSIX qw(setsid); POSIX::setsid(); exec { $ARGV[0] } @ARGV' -- \
        "$INNER" "$pidfile" "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" &
      launcher_pid=$!
      sess=1
      how="perl-setsid"
    else
      nohup "$INNER" "$pidfile" "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" >/dev/null 2>&1 &
      launcher_pid=$!
      sess=0
      how="nohup"
    fi

    pid=""
    for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
      pid="$(peer_read_number "$pidfile")"
      [ -n "$pid" ] && break
      sleep 0.01
    done
    if [ -z "$pid" ]; then
      # Preserve a diagnostic PID if the detached command failed before it
      # could record its leader. Fail-closed: never guess a process group.
      pid="$launcher_pid"
      sess=0
      printf '%s\n' "$pid" > "$pidfile"
    fi
    printf '%s\n' "$sess" > "$sessfile"

    # Watchdog enforces the maximum lifetime even when the caller is delayed.
    # It honors peer.session the same way terminate_recorded does.
    if command -v setsid >/dev/null 2>&1; then
      setsid "$WATCHDOG" "$DEADLINE_SECONDS" "$donefile" "$pidfile" "$childpidfile" "$sessfile" >/dev/null 2>&1 &
      watchdog_pid=$!
    elif command -v perl >/dev/null 2>&1; then
      perl -e 'use POSIX qw(setsid); POSIX::setsid(); exec { $ARGV[0] } @ARGV' -- \
        "$WATCHDOG" "$DEADLINE_SECONDS" "$donefile" "$pidfile" "$childpidfile" "$sessfile" >/dev/null 2>&1 &
      watchdog_pid=$!
    else
      nohup "$WATCHDOG" "$DEADLINE_SECONDS" "$donefile" "$pidfile" "$childpidfile" "$sessfile" >/dev/null 2>&1 &
      watchdog_pid=$!
    fi
    printf '%s\n' "$watchdog_pid" > "$watchdogfile"

    printf 'launched slug=%s pid=%s deadline=%s detach=%s\n' "$SLUG" "$pid" "$deadline_epoch" "$how"
    ;;

  status)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    state="$(resolve_state)"
    rc=$?
    printf '%s\n' "$state"
    exit "$rc"
    ;;

  verdict)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    state="$(resolve_state)"
    output_bytes="$(bytes "$outfile")"
    exit_code="?"
    if [ -f "$donefile" ]; then
      exit_code="$(sed -n 's/^DONE rc=//p' "$donefile" | head -1)"
    fi
    deadline="$(peer_read_number "$deadlinefile")"
    pid="$(peer_read_number "$pidfile")"
    child_pid="$(peer_read_number "$childpidfile")"
    if [ "$JSON" = true ]; then
      printf '{"schema":"v1-peer-run/v1","slug":"%s","state":"%s","output_bytes":%s,"exit_code":%s,"deadline_epoch":%s,"pid":%s,"child_pid":%s}\n' \
        "$SLUG" "$state" "$output_bytes" "$(json_number_or_null "$exit_code")" \
        "$(json_number_or_null "$deadline")" "$(json_number_or_null "$pid")" "$(json_number_or_null "$child_pid")"
    else
      case "$state" in
        complete) printf 'complete (content=%s bytes, rc=%s)\n' "$output_bytes" "$exit_code" ;;
        running) printf 'running (no terminal sentinel yet; process is alive)\n' ;;
        empty_output) printf 'empty_output (exited rc=%s with no substantive output)\n' "$exit_code" ;;
        timed_out) printf 'timed_out (deadline exceeded)\n' ;;
        *) printf 'stalled (vanished without substantive output or terminal sentinel)\n' ;;
      esac
    fi
    exit 0
    ;;

  teardown)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    killed="$(terminate_recorded)"
    if [ -n "$killed" ]; then
      printf 'terminated slug=%s %s\n' "$SLUG" "$killed"
    else
      printf 'already-gone slug=%s\n' "$SLUG"
    fi
    ;;

  *)
    die "unknown subcommand: $cmd (launch|status|verdict|teardown)"
    ;;
esac
