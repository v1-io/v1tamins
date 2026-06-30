#!/usr/bin/env bash
# peer-run.sh — launch and supervise a peer agent as a detached background process.
#
# Encodes the v1-phone-a-friend run-supervision contract once, so peer runs are
# not hand-assembled per invocation. Peer-agnostic: you pass the full peer
# command; this script owns stdin handling, detachment, sentinels, polling,
# PID-scoped teardown, and a completion verdict that trusts substantive output
# over exit code.
#
# WHY DETACHMENT MATTERS: a host command-timeout (e.g. an agent's 2-minute Bash
# default) kills the parent shell's process group. A peer launched with a bare
# `( ... ) &` stays in that group and dies with the parent — the exact stall this
# skill exists to prevent. `launch` puts the peer in its own session/group
# (setsid when available; nohup + a detached subshell as the portable fallback)
# so a parent-shell timeout cannot reap it. On hosts without setsid AND for runs
# that may exceed the command timeout, also use your host's own background
# primitive (e.g. Claude Code's run_in_background) — detachment here is
# best-effort-portable, not a guarantee on every shell.
#
# Multi-peer: call `launch` once per peer with a distinct --slug under one
# --dir; each peer gets its own run subdirectory, .pid, and .done. Then poll
# each slug. Slugs are isolated, so one peer stalling never blocks another.
#
# Usage:
#   peer-run.sh launch   --dir <rundir> --slug <slug> -- <peer-command...>
#   peer-run.sh status   --dir <rundir> --slug <slug>     # running|complete|stalled
#   peer-run.sh verdict  --dir <rundir> --slug <slug>     # complete|stalled + reason (content over exit code)
#   peer-run.sh teardown --dir <rundir> --slug <slug>     # PID-scoped kill (never pattern-kill)
#
# Exit codes: 0 ok; 2 usage error; 3 unknown slug.

set -u

die() { printf 'peer-run: %s\n' "$1" >&2; exit "${2:-2}"; }

# --- arg parsing -------------------------------------------------------------
cmd="${1:-}"; shift || true
RUNDIR=""; SLUG=""
PEER_CMD=()
while [ $# -gt 0 ]; do
  case "$1" in
    --dir)  RUNDIR="${2:-}"; shift 2 || die "--dir needs a value" ;;
    --slug) SLUG="${2:-}";  shift 2 || die "--slug needs a value" ;;
    --)     shift; PEER_CMD=("$@"); break ;;
    *)      die "unexpected arg: $1" ;;
  esac
done

[ -n "$cmd" ]    || die "missing subcommand (launch|status|verdict|teardown)"
[ -n "$RUNDIR" ] || die "--dir is required"
[ -n "$SLUG" ]   || die "--slug is required"

peerdir="$RUNDIR/$SLUG"
pidfile="$peerdir/peer.pid"
donefile="$peerdir/peer.done"
outfile="$peerdir/peer.stdout"
errfile="$peerdir/peer.stderr"

# Substantive-output threshold: a peer that wrote at least this many bytes to
# stdout is treated as having produced real content even under an odd exit code.
MIN_CONTENT_BYTES="${PEER_RUN_MIN_CONTENT_BYTES:-40}"

bytes() { [ -f "$1" ] && wc -c < "$1" | tr -d ' ' || echo 0; }

case "$cmd" in
  launch)
    [ "${#PEER_CMD[@]}" -gt 0 ] || die "launch needs: -- <peer-command...>"
    mkdir -p "$peerdir" || die "cannot create $peerdir"
    : > "$outfile"; : > "$errfile"; rm -f "$donefile"

    # Inner runner: receives out/err/done paths as the first three args, then the
    # peer command. Runs the peer with stdin closed (< /dev/null) so CLIs that
    # probe stdin do not stall, captures both streams, and writes a DONE sentinel
    # with the real exit code the PARENT reads later (the peer never guesses its
    # own rc). Paths are passed as args, not interpolated, so spaces are safe.
    inner='of="$1"; ef="$2"; df="$3"; shift 3; "$@" >"$of" 2>"$ef" </dev/null; printf "DONE rc=%s\n" "$?" >"$df"'

    if command -v setsid >/dev/null 2>&1; then
      # New session/process group: a parent-shell timeout cannot reap it.
      setsid sh -c "$inner" sh "$outfile" "$errfile" "$donefile" "${PEER_CMD[@]}" &
      pid=$!
    else
      # Portable fallback (e.g. macOS, no setsid): nohup ignores SIGHUP and the
      # backgrounded job is disowned so a parent-shell exit does not signal it.
      # Not a full new-session guarantee — see header note.
      nohup sh -c "$inner" sh "$outfile" "$errfile" "$donefile" "${PEER_CMD[@]}" >/dev/null 2>&1 &
      pid=$!
      disown "$pid" 2>/dev/null || true
    fi

    printf '%s\n' "$pid" > "$pidfile"
    printf 'launched slug=%s pid=%s dir=%s\n' "$SLUG" "$pid" "$peerdir"
    ;;

  status)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    if [ -f "$donefile" ]; then
      echo complete; exit 0
    fi
    pid="$(cat "$pidfile" 2>/dev/null || echo)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      echo running
    else
      # process gone but no .done sentinel -> it vanished without finishing
      echo stalled
    fi
    ;;

  verdict)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    out_bytes="$(bytes "$outfile")"
    if [ "$out_bytes" -ge "$MIN_CONTENT_BYTES" ]; then
      # Content over exit code: substantive output means complete even if the
      # wrapper exit code was nonzero or unusual.
      rc="?"; [ -f "$donefile" ] && rc="$(sed -n 's/^DONE rc=//p' "$donefile" | head -1)"
      printf 'complete (content=%s bytes, rc=%s)\n' "$out_bytes" "$rc"
      exit 0
    fi
    if [ -f "$donefile" ]; then
      printf 'stalled (exited rc=%s but no substantive output)\n' "$(sed -n 's/^DONE rc=//p' "$donefile" | head -1)"
    else
      printf 'stalled (no .done sentinel, no substantive output)\n'
    fi
    exit 0
    ;;

  teardown)
    # PID-scoped only. Never `pkill -f`/`killall` — a pattern kill can reap an
    # unrelated peer process the user is running elsewhere.
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    pid="$(cat "$pidfile" 2>/dev/null || echo)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      printf 'terminated slug=%s pid=%s\n' "$SLUG" "$pid"
    else
      printf 'already-gone slug=%s\n' "$SLUG"
    fi
    ;;

  *)
    die "unknown subcommand: $cmd (launch|status|verdict|teardown)"
    ;;
esac
