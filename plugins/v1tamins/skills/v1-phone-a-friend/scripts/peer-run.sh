#!/usr/bin/env bash
# peer-run.sh — launch and supervise one detached peer process.
#
# The caller supplies a complete provider wrapper. This helper owns stdin
# closure, detached sessions, bounded deadlines, sentinels, typed verdicts,
# and PID/PGID-scoped teardown. It never searches for or kills a command-line
# pattern.

set -u

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

alive() {
  local pid="$1"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

has_content() {
  [ -s "$1" ] && LC_ALL=C grep -q '[^[:space:]]' "$1" 2>/dev/null
}

read_number() {
  local file="$1"
  local value=""
  [ -f "$file" ] && value="$(sed -n '1p' "$file")"
  case "$value" in
    ''|*[!0-9]*) printf '\n' ;;
    *) printf '%s\n' "$value" ;;
  esac
}

deadline_expired() {
  local deadline
  deadline="$(read_number "$deadlinefile")"
  [ -n "$deadline" ] || return 1
  [ "$(date +%s)" -ge "$deadline" ]
}

recorded_pids() {
  local pid cpid
  pid="$(read_number "$pidfile")"
  cpid="$(read_number "$childpidfile")"
  printf '%s\n%s\n' "$pid" "$cpid"
}

terminate_recorded() {
  local pid cpid sess watchdog killed=""
  pid="$(read_number "$pidfile")"
  cpid="$(read_number "$childpidfile")"
  sess="$(cat "$sessfile" 2>/dev/null || printf '0')"
  watchdog="$(read_number "$watchdogfile")"

  if alive "$watchdog"; then
    kill -TERM "$watchdog" 2>/dev/null || true
  fi
  if [ "$sess" = "1" ] && [ -n "$pid" ]; then
    if kill -TERM -- "-$pid" 2>/dev/null; then
      killed="pgid=$pid"
    fi
  fi
  for target in "$cpid" "$pid"; do
    if alive "$target"; then
      kill -TERM "$target" 2>/dev/null || true
      killed="${killed:+$killed }pid=$target"
    fi
  done

  # Give the recorded processes a short grace period, then use the same
  # recorded PGID/PIDs for escalation. No command-line or broad process scan.
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if ! alive "$pid" && ! alive "$cpid"; then
      break
    fi
    sleep 0.1
  done
  if [ "$sess" = "1" ] && [ -n "$pid" ] && alive "$pid"; then
    kill -KILL -- "-$pid" 2>/dev/null || true
  fi
  for target in "$cpid" "$pid"; do
    if alive "$target"; then
      kill -KILL "$target" 2>/dev/null || true
    fi
  done
  printf '%s\n' "$killed"
}

resolve_state() {
  local cpid lpid
  cpid="$(read_number "$childpidfile")"
  lpid="$(read_number "$pidfile")"

  # A done sentinel is stronger than a deadline: the peer exited and the
  # wrapper recorded its result. Substantive output, not the exit code, makes
  # that terminal result complete.
  if [ -f "$donefile" ] && has_content "$outfile"; then
    printf 'complete\n'
    return 0
  fi

  if deadline_expired; then
    if alive "$cpid" || alive "$lpid" || [ ! -f "$donefile" ]; then
      printf 'timed_out\n'
      return 1
    fi
  fi

  if alive "$cpid" || alive "$lpid"; then
    printf 'running\n'
    return 2
  fi

  if [ -f "$donefile" ]; then
    printf 'empty_output\n'
    return 1
  fi
  if has_content "$outfile"; then
    printf 'complete\n'
    return 0
  fi
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
    mkdir -p "$peerdir" || die "cannot create run directory"
    : > "$outfile"
    : > "$errfile"
    rm -f "$donefile" "$childpidfile" "$watchdogfile"
    deadline_epoch=$(( $(date +%s) + DEADLINE_SECONDS ))
    printf '%s\n' "$deadline_epoch" > "$deadlinefile"

    # The inner runner backgrounds only the real peer so its PID can be
    # recorded before waiting. stdin is closed at the final child boundary.
    inner='of="$1"; ef="$2"; df="$3"; cf="$4"; shift 4; "$@" >"$of" 2>"$ef" </dev/null & cpid=$!; printf "%s\n" "$cpid" >"$cf"; wait "$cpid"; printf "DONE rc=%s\n" "$?" >"$df"'
    sess=0
    if command -v setsid >/dev/null 2>&1; then
      setsid sh -c "$inner" sh "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" &
      pid=$!
      sess=1
      how="setsid"
    elif command -v perl >/dev/null 2>&1; then
      perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV or die "exec: $!"' \
        sh -c "$inner" sh "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" &
      pid=$!
      sess=1
      how="perl-setsid"
    else
      nohup sh -c "$inner" sh "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" >/dev/null 2>&1 &
      pid=$!
      how="nohup (best-effort; use the host background primitive)"
    fi

    printf '%s\n' "$pid" > "$pidfile"
    printf '%s\n' "$sess" > "$sessfile"

    # The watchdog is itself detached and records no peer output. It enforces
    # the maximum lifetime even when the caller is delayed before polling.
    watchdog='seconds="$1"; df="$2"; pf="$3"; ccf="$4"; sleep "$seconds"; [ -f "$df" ] && exit 0; target="$(sed -n "1p" "$pf" 2>/dev/null)"; child="$(sed -n "1p" "$ccf" 2>/dev/null)"; case "$target" in ""|*[!0-9]*) exit 0 ;; esac; kill -TERM -- "-$target" 2>/dev/null || true; kill -TERM "$child" 2>/dev/null || true; sleep 1; kill -KILL -- "-$target" 2>/dev/null || true; kill -KILL "$child" 2>/dev/null || true'
    if command -v setsid >/dev/null 2>&1; then
      setsid sh -c "$watchdog" sh "$DEADLINE_SECONDS" "$donefile" "$pidfile" "$childpidfile" >/dev/null 2>&1 &
      watchdog_pid=$!
    elif command -v perl >/dev/null 2>&1; then
      perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV or die "exec: $!"' \
        sh -c "$watchdog" sh "$DEADLINE_SECONDS" "$donefile" "$pidfile" "$childpidfile" >/dev/null 2>&1 &
      watchdog_pid=$!
    else
      nohup sh -c "$watchdog" sh "$DEADLINE_SECONDS" "$donefile" "$pidfile" "$childpidfile" >/dev/null 2>&1 &
      watchdog_pid=$!
    fi
    printf '%s\n' "$watchdog_pid" > "$watchdogfile"

    printf 'launched slug=%s pid=%s deadline=%s detach=%s\n' "$SLUG" "$pid" "$deadline_epoch" "$how"
    ;;

  status)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    state="$(resolve_state)"
    rc=$?
    if [ "$state" = "timed_out" ]; then
      terminate_recorded >/dev/null
    fi
    printf '%s\n' "$state"
    exit "$rc"
    ;;

  verdict)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    state="$(resolve_state)"
    resolve_rc=$?
    if [ "$state" = "timed_out" ]; then
      terminate_recorded >/dev/null
    fi
    output_bytes="$(bytes "$outfile")"
    exit_code="?"
    if [ -f "$donefile" ]; then
      exit_code="$(sed -n 's/^DONE rc=//p' "$donefile" | head -1)"
    fi
    deadline="$(read_number "$deadlinefile")"
    pid="$(read_number "$pidfile")"
    child_pid="$(read_number "$childpidfile")"
    if [ "$JSON" = true ]; then
      printf '{"schema":"v1-peer-run/v1","slug":"%s","state":"%s","output_bytes":%s,"exit_code":%s,"deadline_epoch":%s,"pid":%s,"child_pid":%s}\n' \
        "$SLUG" "$state" "$output_bytes" "$(json_number_or_null "$exit_code")" \
        "$(json_number_or_null "$deadline")" "$(json_number_or_null "$pid")" "$(json_number_or_null "$child_pid")"
    else
      case "$state" in
        complete) printf 'complete (content=%s bytes, rc=%s)\n' "$output_bytes" "$exit_code" ;;
        running) printf 'running (no terminal sentinel yet; process is alive)\n' ;;
        empty_output) printf 'empty_output (exited rc=%s with no substantive output)\n' "$exit_code" ;;
        timed_out) printf 'timed_out (deadline exceeded; recorded process was terminated)\n' ;;
        *) printf 'stalled (vanished without substantive output or terminal sentinel)\n' ;;
      esac
    fi
    # Verdict is a report command; callers consume the typed state rather than
    # branching on a provider's exit code.
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
