#!/usr/bin/env bash
# Inner peer process recorder. Invoked by peer-run.sh after detach.
# Args: pidfile outfile errfile donefile childpidfile -- command...

set -u

pidfile="$1"
outfile="$2"
errfile="$3"
donefile="$4"
childpidfile="$5"
shift 5

printf '%s\n' "$$" >"$pidfile"
"$@" >"$outfile" 2>"$errfile" </dev/null &
cpid=$!
printf '%s\n' "$cpid" >"$childpidfile"
wait "$cpid"
printf 'DONE rc=%s\n' "$?" >"$donefile"
