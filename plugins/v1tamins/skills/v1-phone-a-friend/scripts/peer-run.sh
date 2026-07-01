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
# skill exists to prevent. `launch` puts the peer in its OWN session/process
# group so a parent-shell timeout cannot reap it, trying in order:
#   1. setsid (Linux)                      — true new session
#   2. perl POSIX::setsid (macOS has perl) — true new session
#   3. nohup + disown (last resort)        — NOT a new session; survives SIGHUP
#      only. On this path detachment is best-effort, so for runs that may exceed
#      the host command timeout, ALSO use your host's background primitive
#      (e.g. Claude Code's run_in_background). `launch` reports which path it took.
#
# Multi-peer: call `launch` once per peer with a distinct --slug under one
# --dir; each peer gets its own run subdirectory and sentinels. Slugs are
# isolated, so one peer stalling never blocks another.
#
# Usage:
#   peer-run.sh launch   --dir <rundir> --slug <slug> -- <peer-command...>
#   peer-run.sh status   --dir <rundir> --slug <slug>     # running|complete|stalled
#   peer-run.sh verdict  --dir <rundir> --slug <slug>     # state + reason (content over exit code)
#   peer-run.sh teardown --dir <rundir> --slug <slug>     # PID/PGID-scoped kill (never pattern-kill)
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
pidfile="$peerdir/peer.pid"          # the launched leader (session leader on the setsid paths)
childpidfile="$peerdir/peer.child.pid"  # the ACTUAL peer process, so teardown reaps it
sessfile="$peerdir/peer.session"     # "1" = real new session (group kill is safe), "0" = fallback
donefile="$peerdir/peer.done"
outfile="$peerdir/peer.stdout"
errfile="$peerdir/peer.stderr"

# Substantive-output threshold, in bytes. NOTE: this assumes PLAIN-TEXT peer
# output. stream-json/--json modes emit framing events (often >40 bytes) before
# any review content, which would read as "complete" prematurely — so consume
# text output for the verdict and use stream-json only for a live progress
# stream (see references/command-templates.md). Once a peer has exited, any
# non-whitespace output counts as complete so concise smoke tests do not look
# stalled just because they are shorter than the running-output threshold.
MIN_CONTENT_BYTES="${PEER_RUN_MIN_CONTENT_BYTES:-40}"

bytes() { [ -f "$1" ] && wc -c < "$1" | tr -d ' ' || echo 0; }
alive() { p="$1"; [ -n "$p" ] && kill -0 "$p" 2>/dev/null; }
has_content() { [ -s "$1" ] && LC_ALL=C grep -q '[^[:space:]]' "$1" 2>/dev/null; }

# Single source of truth for "what state is this peer in?" — status and verdict
# both resolve through this, so they can never disagree (a live peer is always
# `running`, never falsely `stalled`).
#   prints: running | complete | stalled    returns: 0 complete, 1 stalled, 2 running
resolve_state() {
  ob="$(bytes "$outfile")"
  if [ "$ob" -ge "$MIN_CONTENT_BYTES" ]; then echo complete; return 0; fi
  if [ -f "$donefile" ] && has_content "$outfile"; then echo complete; return 0; fi
  cpid="$(cat "$childpidfile" 2>/dev/null || echo)"
  lpid="$(cat "$pidfile" 2>/dev/null || echo)"
  if alive "$cpid" || alive "$lpid"; then echo running; return 2; fi
  echo stalled; return 1   # not alive, and no substantive output (done-but-empty, or vanished)
}

case "$cmd" in
  launch)
    [ "${#PEER_CMD[@]}" -gt 0 ] || die "launch needs: -- <peer-command...>"
    mkdir -p "$peerdir" || die "cannot create $peerdir"
    : > "$outfile"; : > "$errfile"; rm -f "$donefile" "$childpidfile"

    # Inner runner: out/err/done/childpid paths as the first four args, then the
    # peer command. Backgrounds the peer so it can record the peer's REAL pid
    # (teardown must reap the peer itself, not this wrapper), runs it with stdin
    # closed (< /dev/null), then writes a DONE sentinel with the real exit code
    # the PARENT reads later. Paths are args, not interpolated, so spaces are safe.
    inner='of="$1"; ef="$2"; df="$3"; cf="$4"; shift 4; "$@" >"$of" 2>"$ef" </dev/null & cpid=$!; printf "%s\n" "$cpid" >"$cf"; wait "$cpid"; printf "DONE rc=%s\n" "$?" >"$df"'

    sess=0
    if command -v setsid >/dev/null 2>&1; then
      setsid sh -c "$inner" sh "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" &
      pid=$!; sess=1; how="setsid"
    elif command -v perl >/dev/null 2>&1; then
      # macOS has no setsid but ships perl; POSIX::setsid creates a real new
      # session/group, then exec replaces perl with the wrapper (pid stays valid).
      perl -MPOSIX -e 'POSIX::setsid(); exec @ARGV or die "exec: $!"' \
        sh -c "$inner" sh "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" &
      pid=$!; sess=1; how="perl-setsid"
    else
      nohup sh -c "$inner" sh "$outfile" "$errfile" "$donefile" "$childpidfile" "${PEER_CMD[@]}" >/dev/null 2>&1 &
      pid=$!; sess=0; how="nohup (best-effort; pair with host background primitive)"
      disown "$pid" 2>/dev/null || true
    fi

    printf '%s\n' "$pid"  > "$pidfile"
    printf '%s\n' "$sess" > "$sessfile"
    printf 'launched slug=%s pid=%s detach=%s dir=%s\n' "$SLUG" "$pid" "$how" "$peerdir"
    ;;

  status)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    resolve_state   # already prints running|complete|stalled
    ;;

  verdict)
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    resolve_state >/dev/null; rc=$?
    ob="$(bytes "$outfile")"
    drc="?"; [ -f "$donefile" ] && drc="$(sed -n 's/^DONE rc=//p' "$donefile" | head -1)"
    case "$rc" in
      0) printf 'complete (content=%s bytes, rc=%s)\n' "$ob" "$drc" ;;
      2) printf 'running (no substantive output yet; still alive)\n' ;;
      *) if [ -f "$donefile" ]; then
           printf 'stalled (exited rc=%s but no substantive output)\n' "$drc"
         else
           printf 'stalled (vanished: no output, no .done sentinel)\n'
         fi ;;
    esac
    exit 0
    ;;

  teardown)
    # PID/PGID-scoped only. Never `pkill -f`/`killall` — a pattern kill can reap
    # an unrelated peer the user is running elsewhere.
    [ -f "$pidfile" ] || die "unknown slug: $SLUG" 3
    pid="$(cat "$pidfile" 2>/dev/null || echo)"
    cpid="$(cat "$childpidfile" 2>/dev/null || echo)"
    sess="$(cat "$sessfile" 2>/dev/null || echo 0)"
    killed=""
    if [ "$sess" = "1" ] && [ -n "$pid" ]; then
      # Real new session: the leader's pid IS the process-group id, so a negative
      # signal reaps the peer AND any grandchildren it spawned — still PID-derived.
      kill -TERM -- "-$pid" 2>/dev/null && killed="pgid=$pid"
    fi
    # Always also target the real peer pid and the leader by PID (covers the
    # nohup fallback, where there is no separate group to signal).
    for p in "$cpid" "$pid"; do
      if alive "$p"; then kill "$p" 2>/dev/null && killed="${killed:+$killed }pid=$p"; fi
    done
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
