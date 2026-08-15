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
VERDICT_HELPER="$SCRIPT_DIR/peer_verdict.py"
# shellcheck source=peer-run-lib.sh
. "$SCRIPT_DIR/peer-run-lib.sh"

die() {
  printf 'peer-run: %s\n' "$1" >&2
  exit "${2:-2}"
}

# A missing classifier must fail loudly. Falling back would silently report
# every terminal answer as empty_output.
[ -f "$VERDICT_HELPER" ] || die "missing peer_verdict.py beside peer-run.sh"

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
# terminal answer payload, not framing, progress, reasoning, tool, or error-only
# events. peer_verdict.py owns the shapes; this stays a thin call.
has_peer_answer() {
  local path="$1"
  has_content "$path" || return 1
  python3 "$VERDICT_HELPER" answer "$path"
}

# Envelope family plus which side of the dispatch boundary this run reached.
# Reporting only: neither value changes the resolved state.
peer_report() {
  local exit_code="$1"
  local args=(report "$outfile" "$errfile")
  case "$exit_code" in
    ''|*[!0-9-]*) ;;
    *) args+=(--exit-code "$exit_code") ;;
  esac
  python3 "$VERDICT_HELPER" "${args[@]}" 2>/dev/null || printf 'unknown unknown none\n'
}

# Reject anything the classifier did not produce before it reaches JSON.
peer_token() {
  case "$1" in
    ''|*[!a-z_]*) printf 'unknown\n' ;;
    *) printf '%s\n' "$1" ;;
  esac
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
    read -r envelope_family dispatch_state dispatch_evidence <<EOF
$(peer_report "$exit_code")
EOF
    envelope_family="$(peer_token "$envelope_family")"
    dispatch_state="$(peer_token "$dispatch_state")"
    dispatch_evidence="$(peer_token "$dispatch_evidence")"
    if [ "$JSON" = true ]; then
      printf '{"schema":"v1-peer-run/v1","slug":"%s","state":"%s","envelope_family":"%s","dispatch_state":"%s","dispatch_evidence":"%s","output_bytes":%s,"exit_code":%s,"deadline_epoch":%s,"pid":%s,"child_pid":%s}\n' \
        "$SLUG" "$state" "$envelope_family" "$dispatch_state" "$dispatch_evidence" \
        "$output_bytes" "$(json_number_or_null "$exit_code")" \
        "$(json_number_or_null "$deadline")" "$(json_number_or_null "$pid")" "$(json_number_or_null "$child_pid")"
    else
      case "$state" in
        complete) printf 'complete (content=%s bytes, rc=%s)\n' "$output_bytes" "$exit_code" ;;
        running) printf 'running (no terminal sentinel yet; process is alive)\n' ;;
        empty_output) printf 'empty_output (exited rc=%s with no substantive output; envelope=%s, dispatch=%s)\n' "$exit_code" "$envelope_family" "$dispatch_state" ;;
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
